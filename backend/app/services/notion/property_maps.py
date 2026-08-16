ACCOUNT_PROPERTY_MAP = {
    "name": "이름", "institution": "금융기관", "account_type": "계좌유형",
    "currency": "통화", "source_type": "데이터소스", "is_active": "활성화",
    "include_in_net_worth": "포함여부", "memo": "메모",
}

ASSET_PROPERTY_MAP = {
    "name": "자산명", "account": "계좌", "asset_type": "종류", "asset_class": "자산군",
    "amount_native": "평가금액", "currency": "통화", "liquidity": "유동성",
    "include_in_net_worth": "순자산 포함", "valued_at": "기준일",
}

SAVINGS_PROPERTY_MAP = {
    "name": "상품명", "account": "Accounts", "product_type": "상품유형",
    "current_balance": "현재잔액", "initial_deposit": "초기납입액",
    "monthly_contribution": "월납입액", "base_rate": "기본금리", "bonus_rate": "우대금리",
    "opened_at": "가입일", "maturity_at": "만기일", "interest_method": "이자방식",
    "contribution_method": "납입방식", "tax_type": "세금유형", "status": "상태",
    "include_in_net_worth": "순자산 포함",
}

DEBT_PROPERTY_MAP = {
    "name": "부채명", "account": "계좌", "institution": "금융기관", "debt_type": "부채유형",
    "original_balance": "최초대출금", "current_balance": "현재잔액", "annual_rate": "금리",
    "repayment_type": "상환방식", "monthly_payment": "월상환액", "opened_at": "시작일",
    "maturity_at": "만기일", "status": "상태", "include_in_net_worth": "순자산 반영",
}

GOAL_PROPERTY_MAP = {
    "name": "목표명", "goal_type": "목표유형", "target_amount": "목표금액",
    "starting_amount": "시작금액", "start_date": "시작일", "target_date": "목표일",
    "status": "상태", "memo": "메모",
}

ALLOCATION_PROPERTY_MAP = {
    "name": "목표명", "classification_type": "분류유형", "target_key": "대상",
    "target_weight": "목표비중", "minimum_weight": "최소비중", "maximum_weight": "최대비중",
    "priority": "우선순위", "is_active": "활성화", "effective_from": "적용 시작일",
}

PROPERTY_MAPS = {
    "accounts": ACCOUNT_PROPERTY_MAP,
    "assets": ASSET_PROPERTY_MAP,
    "savings": SAVINGS_PROPERTY_MAP,
    "debts": DEBT_PROPERTY_MAP,
    "goals": GOAL_PROPERTY_MAP,
    "allocation_targets": ALLOCATION_PROPERTY_MAP,
}
