from Classes_Functions import *

def main_function(total_days = 1):
    sim = Simulator(total_days)
    trans_co = Trans_Co()
    accountant = Accountant()
    state = State(sim=sim, trans_co=trans_co, accountant=accountant)
    # state.sim = sim, state.trans_co = trans_co
    demand = Demand(type='forecast')
    supply = Supply(criteria = 'predicted')
    strategy = Strategy(supply, demand)
    # strategy.demand.type = 'random'# strategy.stock.criteria = 'safety level'
    Warehouse_1 = Warehouse(name = 'nagpur', capacity = 22000,
                            current_capacity = 0, daily_holding_cost_per_volume = 1)
    Store_lis = [Store(name = st, capacity = 2000, daily_holding_cost_per_volume = 6) for st in ten_stores]

    Item.instantiate_items_from_csv(file_name = r'.\data\template_items_list.csv')

    if strategy.supply.criteria == 'stock_level':
        init_max_stock()
    elif strategy.supply.criteria == 'predicted':
        init_predicted_supply()
    else:
        raise NotImplementedError('supply criteria needed for setup')

    d_list_items = [item.__dict__ for item in Item.Master_List]

    Calculate_Space_Total_Holding() # metrics calculator (day0)
    
    print('List of Spaces Created')
    for space in Space.Master_List:
        print(space.__repr__()) 
    print()

    for _d in range(1, Simulator.num_of_days+1):
        print(f"\n_______________________\nDay #{_d}") #before sim.run runs day is one less that _d
        sim.run()
        draw_qnty_bar_chart(show_flag = False, save_flag = True)
        pass
    draw_histogram(show_flag = False, save_flag = True)
    print("Code ran without any errors !!!")

    # for space in Space.Master_List:
    #     print(f"{space.name} = {space.total_daily_holding_cost_list}")
    #     print()

if __name__ == '__main__':
    total_days = 90
    main_function(total_days)

