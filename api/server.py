import math

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .database import get_db
from .models import Operadora, Despesa
from .schemas import (
    OperatorResponse, ExpenseResponse,
    PaginatedOperators, PaginationMeta,
    StatisticsResponse,
)

app = FastAPI(
    title="ANS Operadoras API",
    description="API for querying health plan operators and their expenses.",
    version="1.0.0",
)

# CORS: allow the Vue.js frontend (Vite runs on port 5173 by default)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    """Simple health check to verify the server is running."""
    return {"status": "ok"}


@app.get("/api/operadoras", response_model=PaginatedOperators)
def list_operators(
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    limit: int = Query(10, ge=1, le=100, description="Items per page (max 100)"),
    search: str = Query(None, description="Filter by razao_social or CNPJ"),
    db: Session = Depends(get_db),
):
    """Returns a paginated list of operators, optionally filtered by search term."""
    offset = (page - 1) * limit

    query = db.query(Operadora)

    if search:
        pattern = f"%{search}%"
        query = query.filter(
            Operadora.razao_social.ilike(pattern) | Operadora.cnpj.like(pattern)
        )

    total = query.count()
    operators = query.offset(offset).limit(limit).all()

    return PaginatedOperators(
        data=operators,
        pagination=PaginationMeta(
            total=total,
            page=page,
            limit=limit,
            total_pages=math.ceil(total / limit) if total > 0 else 0,
        ),
    )


@app.get("/api/operadoras/{cnpj}", response_model=OperatorResponse)
def get_operator(cnpj: str, db: Session = Depends(get_db)):
    """Returns details of a single operator by CNPJ."""
    operator = db.query(Operadora).filter_by(cnpj=cnpj).first()

    if not operator:
        raise HTTPException(status_code=404, detail=f"Operator with CNPJ '{cnpj}' not found.")

    return operator


@app.get("/api/operadoras/{cnpj}/despesas", response_model=list[ExpenseResponse])
def get_operator_expenses(cnpj: str, db: Session = Depends(get_db)):
    """Returns the expense history for a specific operator."""
    operator = db.query(Operadora).filter_by(cnpj=cnpj).first()

    if not operator:
        raise HTTPException(status_code=404, detail=f"Operator with CNPJ '{cnpj}' not found.")

    expenses = (
        db.query(Despesa)
        .filter_by(reg_ans=operator.reg_ans)
        .order_by(Despesa.data_trimestre.desc())
        .all()
    )

    return expenses


@app.get("/api/estatisticas", response_model=StatisticsResponse)
def get_statistics(db: Session = Depends(get_db)):
    """Returns aggregated statistics: total, average, top 5 operators, expenses by UF."""
    from sqlalchemy import func

    # Only use the latest quarter (YTD — same logic as queries_analytics.sql)
    latest_quarter = db.query(func.max(Despesa.data_trimestre)).scalar()

    # Base filter: leaf-level accounts (9 chars) + latest quarter
    base_filter = (
        (func.char_length(Despesa.conta_contabil) == 9)
        & (Despesa.data_trimestre == latest_quarter)
    )

    # Total expenses
    total_expenses = (
        db.query(func.sum(Despesa.vl_saldo_final))
        .filter(base_filter)
        .scalar()
    ) or 0

    # Count distinct operators for average calculation
    num_operators = (
        db.query(func.count(func.distinct(Despesa.reg_ans)))
        .filter(base_filter)
        .scalar()
    ) or 1

    average_expenses = total_expenses / num_operators

    # Top 5 operators by total expenses
    top_5_rows = (
        db.query(
            Despesa.reg_ans,
            Operadora.razao_social,
            func.sum(Despesa.vl_saldo_final).label("total_expenses"),
        )
        .join(Operadora, Despesa.reg_ans == Operadora.reg_ans)
        .filter(base_filter)
        .group_by(Despesa.reg_ans, Operadora.razao_social)
        .order_by(func.sum(Despesa.vl_saldo_final).desc())
        .limit(5)
        .all()
    )

    top_5 = [
        {"reg_ans": row.reg_ans, "razao_social": row.razao_social, "total_expenses": row.total_expenses}
        for row in top_5_rows
    ]

    # Distribution by UF
    uf_rows = (
        db.query(
            Operadora.uf,
            func.sum(Despesa.vl_saldo_final).label("total_expenses"),
        )
        .join(Operadora, Despesa.reg_ans == Operadora.reg_ans)
        .filter(base_filter)
        .group_by(Operadora.uf)
        .order_by(func.sum(Despesa.vl_saldo_final).desc())
        .all()
    )

    expenses_by_uf = [
        {"uf": row.uf, "total_expenses": row.total_expenses}
        for row in uf_rows
    ]

    return StatisticsResponse(
        total_expenses=total_expenses,
        average_expenses=average_expenses,
        top_5_operators=top_5,
        expenses_by_uf=expenses_by_uf,
    )
