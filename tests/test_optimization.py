from src.optimization import compute_profit, BASE_PRICES, COST_RATIO


def test_compute_profit_uses_cost_ratio():
    product_id = "PHONE001"
    price = 30000
    demand = 10
    cost = BASE_PRICES[product_id] * COST_RATIO

    profit = compute_profit(price, demand, product_id)

    assert profit == (price - cost) * demand


def test_compute_profit_negative_when_below_cost():
    product_id = "LAPTOP001"
    cost = BASE_PRICES[product_id] * COST_RATIO

    profit = compute_profit(cost - 1000, demand=5, product_id=product_id)

    assert profit < 0
