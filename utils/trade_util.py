def get_target_selling_price(start_price_of_day, average_unit_price):
    return max(round(start_price_of_day, 2), round(average_unit_price * 1.1, 2))


def get_target_buying_price(start_price_of_day, average_unit_price):
    if average_unit_price > 0:
        return min(round(start_price_of_day * 0.95, 2), round(average_unit_price * 0.9, 2))
    return round(start_price_of_day * 0.95, 2)


def get_target_buying_amount(price_per_order, exchange_rate, target_price):
    return int(price_per_order / exchange_rate // target_price)


def get_target_buying_total_value(price_per_order, number_of_purchase, buying_amount_list):
    return round(price_per_order * buying_amount_list[number_of_purchase], 2)
