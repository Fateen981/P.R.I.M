import csv
import pandas as pd
from math import ceil
from random import random, randint, seed
import matplotlib.pyplot as plt

seed(1000)

''' The object codes for the different classes are a (cat, sr)
(catergory, serial)
cat: 1 -> Item | 2 -> Space | 3 -> Warehouse | 4 -> Store | 5 -> Transporter
'''
class Demand():
    all_list = ['random', 'forecast','forecast-disturbed']
    '''add value checking to this and below specification classes'''
    def __init__(self, name = 'Unnamed Demand', type='random'):
        self.name = name
        self.type = type.strip().lower()
        if self.type not in Demand.all_list:
            raise TypeError(f"Demand.type has to be one of {Demand.all_list}")
        if self.type == 'forecast':
            self.forecast_prepocessed_flag = False

class Supply():
    all_list = ['stock_level', 'predicted']
    def __init__(self, name = "Unnamed Supply", sequence='FIFO', criteria = 'stock_level'):
        ''''need to add value checking 
            (see if values entered are in a list_of_options else raise error'''
        self.name = name
        self.sequence = sequence.strip().lower()
        self.criteria = criteria.strip().lower()

        if self.criteria not in Supply.all_list:
            raise NotImplementedError("supply criteria not valid")

        if self.criteria == 'stock_level':
            self.order_quantity = 'max'
        elif self.criteria == 'predicted':
            self.orders_schedule_made_flag = False


class Strategy():
    '''
    where you can specify things like JIC/JIT, Safety Levels, FIFO/LIFO, type of forecasting etc
    demand_type = 'random'
    maybe add some type checking or value checking here to make sure the options entererd are valid/implemented
    '''
    instance = None
    def __init__(self, supply = None, demand = None):
        if demand == None:
            demand = Demand()
            self.demand = demand
        else:
            self.demand = demand

        if supply == None:
            supply = Supply()
            self.supply = supply
        else:
            self.supply = supply

        Strategy.instance = self

    @classmethod
    def get_instance(cls):
        return cls.instance

class Accountant():
    instance = None
    def __init__(self):
        self.daily_total_lost_sales_amount_list = [0.0 for _ in range(Simulator.num_of_days + 1)]
        self.daily_lost_sales_time_list = [[] for _ in range(Simulator.num_of_days+1)]
        
        self.daily_out_of_stock_time_list = [[] for _ in range(Simulator.num_of_days+1)]
        Accountant.instance = self

    @classmethod
    def add_dropped_sales(cls, quantity, item_code_key, store):
        '''this is where you add the dropped sales amount to daily total cost 
        and also add the individual order to the list of lists'''
        template_item = Item.get_first_item_from_code(item_code_key)
        lost_amount = Item.get_item_price(item=template_item, 
                                                    store=store, quantity=quantity)            
        Accountant.instance.daily_total_lost_sales_amount_list[Simulator.instance.day] += lost_amount

        drop_tup = (lost_amount, Simulator.instance.day, store, item_code_key, quantity)
        Accountant.instance.daily_lost_sales_time_list[Simulator.instance.day].append(drop_tup)

    @classmethod
    def add_out_of_stock(cls, item_code_key, skus_needed, destination):
        '''this is where you add the dropped sales amount to daily total cost 
        and also add the individual order to the list of lists'''
        oos_tup = (Simulator.instance.day, destination, item_code_key, skus_needed)        
        Accountant.instance.daily_out_of_stock_time_list[Simulator.instance.day].append(oos_tup)

class State():
    '''
    can have things like sim, trans_co (not Trans_Co), day, maybe even strategy
    '''
    instance = None
    def __init__(self, sim = None, trans_co = None, accountant = None):
        if sim == None:
            self.sim = Simulator.instance
        if trans_co == None:
            self.trans_co = Trans_Co.instance
        if accountant == None:
            if Accountant.instance == None:
                Accountant()
            self.accountant = Accountant.instance
        State.instance = self

    @classmethod
    def get_instance(cls):
        return cls.instance

class Simulator():
    num_of_days = 0
    day = 0
    instance = None
    def __init__(self, num_of_days, day = 0, state =  None, strategy = None):
        Simulator.num_of_days = num_of_days
        Simulator.day = day
        if strategy is not None:
            Simulator.strategy = strategy #best to make this a dictionary or a class
                                            #  so you can have different attrs
        else:
            Simulator.strategy = None # dict()
            #This could eventually where we put the strategy 
                                #option but for now we'll keep this as None
        #   end of the day we make all the transfer out we want to make 
        #   and put in orders for all the things we want to order based on stocks
        Simulator.instance = self

    @classmethod
    def get_instance(cls):
        return Simulator.instance

    @classmethod
    def global_update(cls, sim = None, trans_co = None ):
        ''' not needed, sim is nested in a State() class, 
             can update that if needed'''
        if sim == None:
            sim = Simulator.instance
        else:
            Simulator.instance = sim
        pass

    def run(self):
        Simulator.instance.day += 1
        # do some sending and transfering
        # store has sales so it's out_list goes nowhere, just get's deleted
        #    also the store sales have to be calculated
        # transport has some other location is going to so the time delay aspect
        # should i keep track of lead/lag time 
        for loc in Space.Master_List:
            # every item that is in the in_list get's added to space.inventory
            add_item_skus_in_list_to_space(loc.in_to_list[Simulator.instance.day], loc)
            
            # once added to inventory, that' day's inventory can be added to the space.time_list
        
        ###### the items are added to inventory before start of day, 
        #           and then days sales happen, then at night stock taing happens
        
        # v design parameter
        # war = Warehouse.Warehouse_Master_List[0]
        # store1 = Store.Store_Master_List[0]
        # store2 = Store.Store_Master_List[1]
        self.sales()

        # run end of the day functions like check_stock_level() or other planner functions
        Calculate_Space_Total_Holding()
        #### visualise/book keeping functions can go here

        Plan.check_stock_levels()


    def sales(self):
        #   when the demand is entered, the store.stock and inventory reduces 
        #    and those items are poped into the sold_list
        #    you must ensure that you only have to feed in the quantity of the 
        #    item or the item.item_code that is being bought at a store per day, 
        #    the simulator should apply FIFO or LIFO on the inventory 
        #      (search.pop from front or back)
        #    and also it should make sure that the demand being withdrawn 
        #    isn't more thanLogg the store's stock it can, 
        #    but then that has to be tracked separately not deducted from the stock

        # call sales only for stock_tally, and once per item_code, 
        #   not per item i.e. not for every sku
        if Strategy.instance.demand.type == 'forecast':
            self.sales_forecast()
        elif Strategy.instance.demand.type == 'random':
            self.sales_random()
        else:
            raise NotImplementedError(f'only \'random\' sales not {Strategy.demand.type}')
    
    def sales_forecast(self):
        stores_list = [store for store in Store.Store_Master_List]
        item_codes_list = Item.codes_list
        if Strategy.instance.demand.forecast_prepocessed_flag == False:
            self.forecasted_shipment_dict = {
                stor : {it_cd : get_forecasted_shipments(stor, it_cd) 
                for it_cd in item_codes_list
                }
                for stor in stores_list
            }
            # do whatever one time function has to do
            #     meaning to predict all time demand and then plan orders in advance accordingly
            #     note that we have to do this for the stores first, and then tke those values for the 
            Strategy.instance.demand.forecast_prepocessed_flag = True
        
        # This is the sales code that runs every day
        for stor in stores_list:
            stock_dict = stor.sku_stock_tally
            iter = stock_dict.copy()
            for item_code_k in iter:
                item_sku_stock = stock_dict[item_code_k]
                if item_sku_stock == 0:
                    return
                if item_sku_stock < 0:
                    raise ValueError("why is sku stock less than 0")
                try:
                    quant = get_sales_from_df(item_code_k, stor.id[1])[Simulator.instance.day-1]
                    item_quantity_sale_in_store(item_code = item_code_k, 
                        store = stor, quantity = quant)
                except Exception as e:
                    # print(f'Sale did not happen on day {Simulator.instance.day} ' 
                    #         f'for code {item_code_k} in {stor}')
                    print(f"Logger3:\n{e} ")
                    Accountant.add_dropped_sales(quantity=quant,
                                                 item_code_key=item_code_k, store=stor)

    def sales_random(self):
        stores_list = Store.Store_Master_List
        for store in stores_list:
            stock_dict = store.sku_stock_tally
            iter = stock_dict.copy()
            for item_code_key in iter:
                item_sku_stock = stock_dict[item_code_key]
                if item_sku_stock == 0:
                    return
                if item_sku_stock < 0:
                    raise ValueError("why is sku stock less than 0")
                try:
                    quantity= randint(10,30)
                    item_quantity_sale_in_store(item_code = item_code_key, 
                        store = store, quantity = quantity)
                except Exception as e:
                    # print(f'Sale did not happen on day {Simulator.instance.day} ' 
                    #         f'for code {item_code_key} in {store}')
                    print(f"Logger2:\n{e} ")
                    Accountant.add_dropped_sales(quantity=quantity,
                                                 item_code_key=item_code_key, store=store)

class Item:
    """Item SKU Class
    Attributes:: name = "Unnamed Item", item_code = 0, quantity = 1., cost = 1.,
    price = 1., volume = 1, lead_time = 1."""
    Master_List = []
    sr = 0  #serial number, unique for each sku
    code = 1#same for different SKUs of the same object.
            #tells you what is the thing
    codes_list = []#contains all the item codes created until now
    codes_dict = dict() #key=item.code, value=item.name
    def __init__(self, name = "Unnamed Item", item_code = 0, quantity = 1,
                    cost = 1., price = 1., volume = 1., lead_time = 0):
        self.id = (1,Item.sr) #unique for each individual item eg. this carton
        Item.sr += 1
        self.name = name.strip().lower()
        self.item_code = item_code #unique for a kind of item eg all boxes of X
                                    #will have the same item_code
        self.item_code = self.generate_item_code()
        if quantity == 0:
            raise ValueError("can't have 0 quantity otherwise maths will break")
        self.quantity = quantity
        self.sku_quantity = quantity
        self.cost = cost # this is per item also for uniformity with below 
        self.price = price # pls make this per item, not per sku
        self.volume = volume
        self.lead_time = lead_time #use days
        self.lead_time = self.get_item_lead_time()
        self.current_location = None #use add_item functions to add to location
        self.daily_holding_cost = self.get_item_daily_holding_cost()

        Item.Master_List.append(self)

    def __repr__(self):
        return (f"Name:{self.name} ID:{self.id} Code: {self.item_code} "
                f"Qnty: {self.quantity}/{self.sku_quantity}")

    def generate_item_code(self):
        ''' if code given, it will use that item_code and add to the codes_list
                note that it does not check if the manually added codes r unique
            if not, it will try and find some other item with the same name and
                use that item's value code
            else it will return the next item code not already used already'''
        if self.item_code == 0:
            #this means default value of 0 is rn the item_code
            name = self.name.strip().lower()
            name_found_flag = 0
            for it in Item.Master_List:
                if it.name == name:
                    name_found_flag = 1
                    return it.item_code
            #this means that item name not found
            #   we need a new unique item code for this item
            if name_found_flag == 0:
                while Item.code in Item.codes_list:
                    Item.code += 1
                Item.codes_list.append(Item.code)
                Item.codes_dict[Item.code] = self.name
                return Item.code
        else:
            #this means that some non default value was entered to the item code
            if self.item_code not in Item.codes_list:
                # the item code is new
                Item.codes_list.append(self.item_code)
                Item.codes_dict[self.item_code] = self.name
            return self.item_code

    def spawn_new_copy(self):
        new_item = Item(
                        name = self.name, item_code = self.item_code,
                        quantity = self.sku_quantity, cost = self.cost, price = self.price, 
                        volume = self.volume, lead_time = self.lead_time)
        # maybe here you should directly set new_item.location = incoming_location
        return new_item

    @classmethod
    def spawn_copy(cls, item):
        return item.spawn_new_copy()    

    #PLACEHOLDER FUNCTION, REPLACE ONCE DECIDED
    def get_item_lead_time(self):
        return self.lead_time

    def get_item_daily_holding_cost(self):
        if self.current_location == None:
            return 0.0
        else:
            try:
                loc = self.current_location
                return loc.daily_holding_cost_per_volume * self.volume
            except:
                raise ValueError(f"{self.id}, {self.name} in {self.current_location} "
                                    f"has an error in get_item_daily_holding_cost in init")

    def get_item_selling_price(self, quantity = None, store = None):
        # this function is incase i make somemistake in price for an item
        # or one sku and then i can just change the calculation here.
        if quantity == None:
            quantity = self.quantity
        if store == None:
            store = self.current_location
        return self.price * quantity

    def update(self):
        '''all the attrs that have to be when added/shifted to loc
        or maybe just at the end of the day if those things change'''
        self.daily_holding_cost = self.get_item_daily_holding_cost()
        self.lead_time = self.get_item_lead_time()

    @classmethod
    def get_item_from_id(cls, id , search_list = Master_List):
        # self.id = (1,Item.sr) #unique for each individual item eg. this carton
        if type(id) == tuple:
            if id[0] != 1:
                raise ValueError('Is this an Item?')
            query_sr = id[1]
        else:
            query_sr = id
        for item in search_list:
            item_sr = item.id[1]
            if (item_sr == query_sr):
                return item
        raise ValueError("Item code not found")

    @classmethod
    def get_first_item_from_code(cls, query_code , search_list = Master_List):
        # self.id = (1,Item.sr) #unique for each individual item eg. this carton
        if Strategy.instance.supply.sequence == 'FIFO':
            search_list = search_list[::-1]
        if query_code not in Item.codes_list:
            raise ValueError("Item code not in codes_list")
        for item in search_list:
            if (item.item_code == query_code):
                return item
        raise ValueError("Item code not found")

    @classmethod
    def get_first_items_list_from_code(cls, query_code, len , search_list = Master_List):
        # self.id = (1,Item.sr) #unique for each individual item eg. this carton
        if Strategy.instance.supply.sequence == 'FIFO':
            search_list = search_list[::-1]
        if query_code not in Item.codes_list:
            raise ValueError("Item code not in codes_list")
        ans_list = []
        num_found = 0
        for item in search_list:
            if (item.item_code == query_code):
                ans_list.append(item)
                num_found += 1
                if num_found == len:
                    return ans_list
        raise ValueError(f"only {num_found} items were found in list in {search_list[0].current_location.name} output ;\n"
                            f" {ans_list}")

    @classmethod
    def instantiate_items_from_csv(Item, file_name = 'items_list.csv'):
        with open(file_name, 'r') as f:
            reader = csv.DictReader(f)
            items_list = list(reader)

        for ind, elem in enumerate(items_list):
            for k in elem:
                try:
                    elem[k] = float(elem[k])
                except:
                    pass
            temp_it = Item(**elem)
        return

    @classmethod
    def get_Item_total(cls,attr):
        total = 0
        for item in cls.Master_List:
            val = getattr(item, attr)
            total += val
        return total

    @classmethod
    def get_item_price(cls, item, store = None, quantity = None):
        if store == None:
            if item.current_location == None:
                raise ValueError(f"How is this happening {item} nowhere")
            else:
                store = item.current_location

        if quantity == None:
            quantity = item.quantity

        ans = item.price * quantity 
        return ans


class Space():
    Master_List = [] #just to keep track of all the storages
    def __init__(self, name = "Unnamed Space", capacity = 1,
                    current_capacity = 0, daily_holding_cost_per_volume = 0):
        self.name = name
        self.capacity = capacity
        self.current_capacity = current_capacity
        self.daily_holding_cost_per_volume = daily_holding_cost_per_volume
        self.inventory_list = list() #this is what you add all the items to
        self.sku_stock_tally = dict()

        num_of_days = Simulator.num_of_days
        if num_of_days <= 0:
            raise ValueError(f'You can\'t have {num_of_days} number of days!')

        self.time_list = [ [] for _ in range(num_of_days + 1) ]
        ###loc.time_list[day].append(item/order)
        self.in_to_list = [ [] for _ in range(num_of_days + 1) ]
        # self.in_to_list = self.time_list.copy()
        ###loc.in_to_list[day].append(item/order)

        # waiting_list is a list that has the tuple v 
        #   used to prevent duplicate orders once an order is place
        # self.waiting_list = [] # (item_code, due date)
        self.waiting_dict = dict() # {item_code : due_date}

        # self.out_from_list = self.time_list.copy()    # bad idea don't know where it's going
        self.total_daily_holding_cost_list = [0.0 for _ in range(num_of_days + 1)]
            # should the default value ^ be None or 0.0
        Space.Master_List.append(self)

    def __repr__(self):
        return f"Name:{self.name} cap:({self.current_capacity}/{self.capacity})"

    def __str__(self):
        return f"{self.name}"

    def get_daily_holding_cost_per_volume(self):
        return self.daily_holding_cost_per_volume    

    def get_total_inventory(self,attr):
        total = 0
        for item in self.inventory_list:
            val = getattr(item, attr)
            total += val
        return total

    @classmethod
    def instantiate_spaces_from_csv(cls, file_name):
        with open(file_name, 'r') as f:
            reader = csv.DictReader(f)
            spaces_list = list(reader)

        for ind, elem in enumerate(spaces_list):
            temp_space = cls(name = f"{file_name}_{ind}")
            for pair in elem.items():
                # f"attr_name : {pair[0]} | value : {pair[1]}"
                attribute = pair[0].strip().lower()
                val = pair[1].strip().lower()
                try:
                    val = float(val)
                except:
                    pass
                setattr(temp_space, attribute, val)


class Warehouse(Space):
    ''' For the warehouse(s) '''
    Warehouse_Master_List = []
    sr = 0 #serial number
    def __init__(self, name = "Unnamed Warehouse", capacity = 1,
                    current_capacity = 0, daily_holding_cost_per_volume = 0):
        super().__init__(name, capacity, current_capacity, daily_holding_cost_per_volume)

        self.id = (3,Warehouse.sr)
        Warehouse.sr += 1
        Warehouse.Warehouse_Master_List.append(self)


class Store(Space):
    ''' For the store(s) '''
    Store_Master_List = []
    sr = 1 #serial number
    def __init__(self, name = "Unnamed Warehouse", capacity = 1,
                    current_capacity = 0, daily_holding_cost_per_volume = 1):
        super().__init__(name, capacity, current_capacity, daily_holding_cost_per_volume)
        self.id = (4,Store.sr)
        Store.sr += 1
        Store.Store_Master_List.append(self)
        num_of_days = Simulator.num_of_days
        self.daily_sold_item_quantity_list = [[] for _ in range(num_of_days + 1)] 
        # ^^^ this contains the tuple (item, qnty, total_price) as elements of the sublist
        self.total_daily_sales_list = [0.0 for _ in range(num_of_days + 1)]


class Incoming_location():
    instance = None
    def __init__(self):
        self.name = 'incoming location'
        self.inventory_list = []
        self.total_daily_holding_cost_list = [0.0 for _ in range(Simulator.num_of_days + 1)]
        Incoming_location.instance = self

    def __repr__(self):
        return self.name + " cap: " + str(len(self.inventory_list))

class Transitioning_location():
    instance = None
    def __init__(self):
        self.name = 'transitioning_location'
        self.total_daily_holding_cost_list = [0.0 for _ in range(Simulator.num_of_days + 1)]
        self.inventory_list = []
        Transitioning_location.instance = self

    def __repr__(self):
        return self.name + " cap: " + str(len(self.inventory_list))


class Trans_Co():
    instance = None
    incoming_location = Incoming_location()
    transitioning_location = Transitioning_location()
    # daily cost has to be calculated
    # send_to_place function that both sends 
    #   and adds the cost of the service to it's own bill
    def __init__(self):
        self.time_list = [ [] for _ in range(Simulator.num_of_days + 1) ]
        self.total_daily_cost_list = [0.0 for _ in range(Simulator.num_of_days + 1)]
        self.cost_of_transp_per_volume = 20 #Rupees per unit volume per day
        # design parameter ^
        Trans_Co.instance = self

    @classmethod
    def get_incoming_location_instance(cls):
        return cls.Incoming_location.instance    

    @classmethod
    def get_instance(cls):
        return cls.instance

    @classmethod
    def send_sku_to_place(cls, item, destination):
        self = cls.instance
        self.add_order_to_time_list(item, destination)
        self.calc_transp_order_cost(item, destination)
        self.send_item_to_loc_in_to_list(item, destination = destination)

    def add_order_to_time_list(self, item, destination):
        origin = item.current_location
        order = (item, origin, destination)
        self.time_list[Simulator.instance.day].append(order)

    def calc_transp_order_cost(self, item, destination, origin = None):
        if origin == None:
            origin = item.current_location
            if origin == None:
                raise ValueError('item has no origin')
        if type(destination) == type(Store.Store_Master_List[0]):
            # destination is a store
            cost = (item.volume 
                    * self.cost_of_transp_per_volume
                    * get_days_from_nagpur(destination) )
        elif type(destination) == type(Warehouse.Warehouse_Master_List[0]):
            cost = (item.quantity
                    * item.cost
                    # * item.lead_time
                    )
        self.total_daily_cost_list[Simulator.instance.day] += cost

    def send_item_to_loc_in_to_list(self, item, destination):
        if type(destination) == type(Store.Store_Master_List[0]):
            # Warehouse -> Stores
            travel_days = get_days_from_nagpur(destination.name)
            due_date = Simulator.instance.day + travel_days

        elif type(destination) == type(Warehouse.Warehouse_Master_List[0]):
            # New item -> Warehouse
            travel_days = item.lead_time
            due_date = Simulator.instance.day + travel_days

        remove_item_sku_from_space(item, item.current_location)
        if (type(destination) == type(Store.Store_Master_List[0])):
           # have one function to replace te below two lines
           Trans_Co.instance.transitioning_location.inventory_list.append(item)
           item.current_location = Trans_Co.instance.transitioning_location


        elif (type(destination) == type(Warehouse.Warehouse_Master_List[0])):
           Trans_Co.instance.incoming_location.inventory_list.append(item)
           item.current_location = Trans_Co.instance.incoming_location

        # else:
        #     raise NotImplementedError('What to do then?')
        
        stretchy_list_append(item, due_date, destination.in_to_list)  
        if item.item_code in destination.waiting_dict:
            return
        else:
            destination.waiting_dict[item.item_code] = due_date
    

class Plan():
    strategy = None # you have also setup a Sim.strategy class attr
    num_of_days = Simulator.num_of_days
    order_daily_list = [ [] for _ in range(num_of_days + 1) ]

    @staticmethod
    def check_stock_levels():
        if Strategy.instance.supply.criteria == 'stock_level':
            for loc in (Warehouse.Warehouse_Master_List + Store.Store_Master_List):
                loc_sku_stock_dict = loc.sku_stock_tally
                for item_code_key in loc_sku_stock_dict:
                    item_sku_stock = loc_sku_stock_dict[item_code_key]
                    Plan.item_code_safety_level_check(item_code_key, item_sku_stock, loc)

        elif Strategy.instance.supply.criteria == 'predicted':
            if Strategy.instance.supply.orders_schedule_made_flag == False:
                Plan.create_forecast_schedule()
                Strategy.instance.supply.orders_schedule_made_flag = True

                # running for day = 0
                today = 0
                for item_code in Item.codes_list:
                    skus_num = Plan.warehouse_requirements_ddict[item_code][today]
                    if skus_num != 0:
                        Plan.order(skus_num, item_code, Warehouse.Warehouse_Master_List[0])
                
                for store in Store.Store_Master_List:
                    for itm_co in Item.codes_list:
                        # place the order if it's in the Plan.
                        skus_num = Plan.store_daily_order_ddict[today][store.id[1]][itm_co]
                        if skus_num != 0:
                            Plan.order(skus_num, itm_co, store)

            # this might be a good place to initialise the items properly to prevent weird start

            # runs every day            
            today = Simulator.instance.day
            for item_code in Item.codes_list:
                skus_num = Plan.warehouse_requirements_ddict[item_code][today]
                if skus_num != 0:
                    Plan.order(skus_num, item_code, Warehouse.Warehouse_Master_List[0])
            
            for store in Store.Store_Master_List:
                for itm_co in Item.codes_list:
                    # place the order if it's in the Plan.
                    skus_num = Plan.store_daily_order_ddict[today][store.id[1]][itm_co]
                    if skus_num != 0:
                        Plan.order(skus_num, itm_co, store)

        else:
            raise NotImplementedError("supply criteria not defined")
            
    @staticmethod
    def create_forecast_schedule():
        sto_list = Store.Store_Master_List
        ite_co_list = Item.codes_list
        dict_of_list_of_shipments = Simulator.instance.forecasted_shipment_dict
        # [store][item_code] -> list(orders expected)

        schedule_ddict = {
            store.id[1] : {item_code:[] for item_code in ite_co_list}
            for store in sto_list
        }

        daily_order_ddict = {
            day : {store.id[1] : {item_code : 0.0 for item_code in ite_co_list}
                for store in sto_list
            }
            for day in range(Simulator.instance.num_of_days+1)
        }

        for a_store in sto_list:
            a_st_no = a_store.id[1]
            t_delay = get_days_from_nagpur(a_store)

            for an_it_co in ite_co_list:
                arrival_shipments_list = dict_of_list_of_shipments[a_store][an_it_co]
                # received_lis = [] # shpmnt = (day, store, item_code, num_skus)
                for shpmnt in arrival_shipments_list:
                    or_day = max( (shpmnt[0] - t_delay) , 0 )
                    shp_store, shp_item_code, shp_num_skus = shpmnt[1:]
                    schedule_ddict[a_st_no][an_it_co].append((
                        or_day, shp_store, shp_item_code, shp_num_skus))
                    # item should be ordered on or_day so that it reaches by day
                    daily_order_ddict[or_day][shp_store.id[1]][shp_item_code] += shp_num_skus

            # schedule_ddict[store_no][item_co] = [(or1), (or2) .... ]
            #                   (or_day, shp_store, shp_item_code, shp_num_skus)
            # daily_order_ddict[or_day][shp_store.id[1]][shp_item_code] = shp_num_skus
        Plan.store_schedule_ddict, Plan.store_daily_order_ddict = schedule_ddict, daily_order_ddict

        warehouse_requirements_ddict = { item_code : {day:0.0 
                    for day in range(Simulator.instance.num_of_days + 1)
                }
            for item_code in Item.codes_list
        }

        for day_no in range(Simulator.instance.num_of_days):
            for stre in Store.Store_Master_List:
                for itm_code in Item.codes_list:
                    template_item = Item.get_first_item_from_code(itm_code)
                    adj_day = max((day_no - template_item.lead_time), 0)
                    warehouse_requirements_ddict[itm_code][adj_day] += \
                        Plan.store_daily_order_ddict[day_no][stre.id[1]][itm_code]

        Plan.warehouse_requirements_ddict = warehouse_requirements_ddict
        # inp[item_code][day] -> total_num_of_skus ordered each day 

        return

    @staticmethod
    def get_max_item_quantity_levels(item_code, space):
        '''
        this returns no of sku, not individual qntty
        '''
        # Design Parameter
        default = 500 # DESIGN PARAMETER
        value = default
        if space.id[0] == 3:
            #it is a warehouse
            return int(value*(len(Store.Store_Master_List)) + value)                                                                 
        return value 

    @staticmethod
    def get_min_item_quantity_levels(item_code,space):
        # default = 50 # DESIGN PARAMETER
        default = 200 # DESIGN PARAMETER
        value = default
        if space.id[0] == 3:
            #it is a warehouse
            return int(2*value*(len(Store.Store_Master_List)) + value)
        return value 

    @staticmethod
    def item_code_safety_level_check(item_code, item_sku_stock, space):
        ''' Plan.function that triggers a Plan.order at the correct time 
             based on the stock_levels and/or the demand forcasted'''
        if item_code in space.waiting_dict:
            return

        if Strategy.instance.supply.criteria == 'stock_level':
            max_item_quantity = Plan.get_max_item_quantity_levels(item_code, space)
            min_item_quantity = Plan.get_min_item_quantity_levels(item_code, space)
            if item_sku_stock > 0:
                recent_item = Item.get_first_item_from_code(item_code, space.inventory_list)
                sku_quantity = recent_item.sku_quantity
                if sku_quantity == 0:
                    raise ZeroDivisionError('Should not occur')
                # make a get item that follows sequence 
                total_current_item_quantity = (
                    (item_sku_stock - 1)* (sku_quantity)
                    + recent_item.quantity
                )
                # this num_units is not including open/consumed items
                if total_current_item_quantity < min_item_quantity:
                    # min max strategy:
                    if Strategy.instance.supply.order_quantity == 'max':
                        total_item_quantity_needed = max_item_quantity - total_current_item_quantity
                        skus_needed = ceil(total_item_quantity_needed/sku_quantity)
                        if skus_needed <= 0:
                            print(f"{skus_needed} skus_needed for {item_code} in {space.name}")
                            return
                        Plan.order(skus_needed, item_code, space)
                    else:
                        raise NotImplementedError('only min max strategy is implemnted right now')
            elif item_sku_stock == 0:
                template_item = Item.get_first_item_from_code(item_code, Item.Master_List)
                sku_quantity = template_item.sku_quantity
                total_current_item_quantity = 0
                skus_needed = ceil(max_item_quantity/sku_quantity)
                Plan.order(skus_needed, item_code, space)
            else:
                raise ValueError("isn't this not supposed to happen")
        else:
            raise NotImplementedError('Strategy.instance.supply.criteria != \'stock_level')

    @staticmethod
    def stock_level_of_item_in_space(item, space):
        return space.sku_stock_tally[item.code]
   
    @staticmethod
    def order(skus_needed, item_code, destination):
        '''
        orders skus_needed amounts of item_code items to destination
        order is an instantaneous thing, we can maybe consider the planner to have them scheduled for 
            whenever it thinks it's best to place the order
        '''
        assert skus_needed > 0
        skus_needed = int(skus_needed)
        items_list = []
        template_item = Item.get_first_item_from_code(item_code, Item.Master_List)

        if type(destination) == type(Warehouse.Warehouse_Master_List[0]):
            # if destination is a warehouse then need to make new items
            for _i in range(skus_needed):
                it = template_item.spawn_new_copy()
                add_item_to_incoming(it) #is this the best place to add to incoming
                # v was this really missing?
                items_list.append(it)

            for nu_item in items_list:
                Plan.schedule_item_to_location(nu_item, destination)

        elif type(destination) == type(Store.Store_Master_List[0]):
            # destination is a store, just send from warehouse to destination
            try:
                items_list = Item.get_first_items_list_from_code(
                    item_code, skus_needed, 
                    Warehouse.Warehouse_Master_List[0].inventory_list
                )
            except Exception as e:
                # print(f"{e} error has occured")
                print(f"Logger1 item_code {item_code}, #skus {skus_needed} to destination {destination}"
                        f" from warehouse but not found")
                Accountant.add_out_of_stock(item_code, skus_needed, destination)

            for ol_item in items_list:
                Plan.schedule_item_to_location(ol_item, destination)

        else:
            raise NotImplementedError('This isn\'t supposed to happen')
        
    @staticmethod
    def schedule_item_to_location(item = None, space = None):
        '''check if this function was eddited unknowingly'''
        destination = space
        if item == None or destination == None:
            raise ValueError("enter item and space in schedule_items_to_location")

        if (
            ( type(destination) == type(Warehouse.Warehouse_Master_List[0]) )
            or
            ( type(destination) == type(Store.Store_Master_List[0]) )
            ):
            Trans_Co.send_sku_to_place(item =item, destination=destination)

        else:
            raise ValueError('There isn\'t supposed to be \
                                another type of location -> {location.name}')

ten_stores = ['delhi', 'mumbai', 'kolkata', 'hyderabad', 'chennai', 'bangalore',
                'ahmedabad', 'indore', 'lucknow', 'kozhikode']

def get_object_id_from_Master_List(M_List, id):
    flag = 0
    for it in M_List:
        if it.id == id:
            flag = 1
            return it
    if flag == 0:
        raise ValueError(F"The id {id} entered is not in the list")

def get_attr_total_in(attr, list_of_item):
    total = 0
    for item in list_of_item:
        val = getattr(item, attr)
        total += val
    return total

def add_item_sku_to_space(item, space):
    '''this is for adding an item to a new location'''
    if type(item) == type([]):
        if len(item) == 1:
            item = item[0]
            print(f'{item} given as a list')
        else:
            raise TypeError("why is item a list here?")

    item_code = item.item_code
    if item_code in space.waiting_dict:
        
        # # v is optional, can delete as doesn't effect code
        # if space.waiting_dict[item_code] != Simulator.instance.day:
        #     print(f'This might be an error\n{space.waiting_dict[item_code]}'
        #             f' is not same as sim day {Simulator.instance.day}')
        # # the item has been added so you can remove from waiting list
        del space.waiting_dict[item_code]
    
    # item removed from old location
    item_current_location = item.current_location
    if item_current_location is not None:
        # item still in old location so remove it from there
        remove_item_sku_from_space(item, item_current_location)

    if item.volume <= (space.capacity - space.current_capacity):
        # there is space in space to hold item
        space.current_capacity += item.volume
        item.current_location = space
        
        # update the space.sku_stock_tally
        if item.item_code in space.sku_stock_tally:
            space.sku_stock_tally[item.item_code] = space.sku_stock_tally[item.item_code] + 1
        else:
            space.sku_stock_tally[item.item_code] = 1
            
        item.update()
        space.inventory_list.append(item)
    else:
        raise ValueError(f"You have added {item.name} to {space.name} which"
                            f" exceeds it's max cap. of {space.capacity}")

def remove_item_sku_from_space(item = None, space = None):
    '''removes sku from space and from Trans_Co locations'''
    if space == None:
        space = item.current_location
    if item.current_location != space:
        raise ValueError(f"{item} to be removed from {space} says"
                                f" it's at {item.current_location}")

    if ((type(space) == type(Incoming_location.instance))
        or (type(space) == type(Transitioning_location.instance))):
        # remove sku from trans_co location 
        item.current_location.inventory_list.remove(item)
        item.current_location = None
        return
    
    if item not in space.inventory_list:
        raise ValueError(f"{item.name} is not in {space.name} inventory")
    else:
        space.current_capacity -= item.volume

        # update the space.sku_stock_tally
        if item.item_code in space.sku_stock_tally:
            space.sku_stock_tally[item.item_code] -= 1
            # if space.sku_stock_tally[item.item_code] <= 0:
            #     # item no longer in stock
            #     del space.sku_stock_tally[item.item_code]
        else:
            raise ValueError(f'How is the {item.name},{item.item_code} item.item_code' 
                                f'not {space.name} sku_stock_tally')

        if space.current_capacity < 0:
            raise ValueError("Wait, how can the capacity be less than 0")

        item.current_location = None
        item.update()
        space.inventory_list.remove(item)

def add_item_skus_in_list_to_space(list_of_items, space):
    ''' list of items get added to a space'''
    for item in list_of_items:
        add_item_sku_to_space(item, space)

def remove_item_skus_in_list_from_space(space, list_of_items):
    for item in list_of_items:
        remove_item_sku_from_space(item, space)

def write_list_of_dict_to_csv(d_list = [], csv_file_name = None):
    # maybe you need to separately arguement in the input the headers
    # or maybe you have to extract and print them at the top here
    if csv_file_name is None:
        csv_file_name = f"dict2csv#{randint(1000,9999)}"
    if d_list == []:
        raise ValueError("empty list given")

    with open(csv_file_name, 'w',newline='') as csvfile:
        # fieldnames = ['first_name', 'last_name']
        fieldnames = list(d_list[0].keys())
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(d_list)
        # for ind, d in enumerate(d_list):
        #     writer.writerow(d)
    print(f"csv file {csv_file_name} created") 
    return

def item_quantity_sale_in_store(item_code, store, quantity = 1):

    item = Item.get_first_item_from_code(item_code, store.inventory_list)
    if quantity <= item.quantity:
        item.quantity -= quantity
        amount = Item.get_item_price(item, store = store, quantity = quantity)
        store.daily_sold_item_quantity_list[Simulator.instance.day].append((item, quantity, amount))
        store.total_daily_sales_list[Simulator.instance.day] += amount
        if item.quantity == 0:
            remove_item_sku_from_space(item, store)

    else:
        skus_list = [sku for sku in store.inventory_list if sku.item_code == item_code]
        if len(skus_list) <= 1:
            raise ValueError(f"Demand of #{quantity} of {item_code} in {store}"
                                f" exceeds stock of skus = {len(skus_list)}")
        needed_sku_list = []
        temp_stock = 0
        index = 0
        while temp_stock < quantity:
            try:
                new_it = skus_list[index]
                temp_stock += new_it.quantity
                needed_sku_list.append(new_it)
                index += 1
            except Exception as e:
                if index >= len(skus_list):
                    break
                # index+=1
                # if str(e) == "list index out of range" break
                print(f"{e} exception has occured, but we're letting it slide")

        if index >= len(skus_list) and temp_stock < quantity:
            raise ValueError(f"not enough items in stock to meet the sale")

        total_amount = 0
        for l_ind, sku in enumerate(needed_sku_list):
            lil_amount = Item.get_item_price(sku, store = store, quantity = sku.quantity) 
            total_amount += lil_amount
            store.daily_sold_item_quantity_list[Simulator.instance.day].append((sku, sku.quantity, lil_amount))
            sku.quantity = 0
            if l_ind+1 == len(needed_sku_list):
                # last item is the one that might not be used up completely
                sku.quantity = (temp_stock-quantity)
            if sku.quantity == 0:
                remove_item_sku_from_space(sku, store)
        store.total_daily_sales_list[Simulator.instance.day] = total_amount
        
def item_in_store_discount_percentage(item, store):
    ###### NOT IMPLEMENTED #######
    # CHECK IF store wide or item wide discount
    # or add all items dicounted in a store to a store.discount_list 
    # and if item in that list of (item, %), then return % else 0
    return 0.0

def get_days_from_nagpur(loc):
    if type(loc) == type(Store.Store_Master_List[0]):
        name = loc.name
    #or you can just import in the distance from the csv and then do the if elif
    elif type(loc) == type(''):
        name = loc.strip().lower()
    else:
        raise ValueError('should have entered a loc obj or a name str')
        name = loc.name.strip().lower()
    one_day_stores = ['delhi', 'lucknow']
    two_day_stores = ['mumbai', 'kolkata', 'hyderabad', 'ahmedabad', 'indore']
    three_day_stores = ['chennai', 'bangalore', 'kozhikode']

    if name in one_day_stores:
        return 1
    elif name in two_day_stores:
        return 2
    elif name in three_day_stores:
        return 3
    else:
        raise ValueError(f"The location {name} is not valid")

def stretchy_list_add(elem, ind, lis, padding = None):
    '''should return an edited list
    lis = stretchy_list_add(elem, ind, lis)'''
    try:
        lis[ind] += elem
        return lis
    except IndexError as e:
        err_str = 'list assignment index out of range'
        if str(e) == err_str:
            length = len(lis)
            if ind < 0:
                # extra_length = ind - length
                raise NotImplementedError('Do you want to pre- or a-ppend')
            else:
                extra_length = ind - length + 1
            lis += [padding] * extra_length
            lis[ind] += elem
            return lis
        else:
            raise OSError("Index Error not Caught!")

def stretchy_list_set(elem, ind, lis, padding = None):
    '''should return an edited list
    lis = stretchy_list_add(elem, ind, lis)'''
    try:
        lis[ind] = elem
        return lis
    except IndexError as e:
        err_str = 'list assignment index out of range'
        if str(e) == err_str:
            length = len(lis)
            if ind < 0:
                # extra_length = ind - length
                raise NotImplementedError('Do you want to pre- or a-ppend')
            else:
                extra_length = ind - length + 1
            lis += [padding] * extra_length
            lis[ind] = elem
            return lis
        else:
            raise OSError("Index Error not Caught!")

def stretchy_list_append(elem, ind, lis, padding = []):
    '''should return an edited list, append means adding elements to a list
    lis = stretchy_list_add(elem, ind, lis)'''
    ind = int(ind)
    try:
        lis[ind].append(elem)
        return lis
    except IndexError as e:
        err_str = 'list index out of range'
        if str(e) == err_str:
            length = len(lis)
            if ind < 0:
                # extra_length = ind - length
                raise NotImplementedError('Do you want to pre- or a-ppend')
            else:
                extra_length = ind - length + 1
            pad_list = list()
            for _ in range(extra_length):
                pad_list += [padding]
            pad_list[-1] = [elem]
            lis.extend(pad_list)
            return lis
        else:
            raise OSError("Index Error not caught")

def stretchy_list_extend(elem, ind, lis, padding = []):
    '''should return an edited list, extend means ading two lists
    lis = stretchy_list_add(elem, ind, lis)'''
    try:
        lis[ind].extend(elem)
        return lis
    except IndexError as e:
        err_str = 'list assignment index out of range'
        if str(e) == err_str:
            length = len(lis)
            if ind < 0:
                # extra_length = ind - length
                raise NotImplementedError('Do you want to pre- or a-ppend')
            else:
                extra_length = ind - length + 1
            lis += [padding] * extra_length
            lis[ind].extend(elem)
            return lis
        else:
            raise OSError("Index Error not Caught!")

def NOPE_get_list_of_num_items_in_space(num_of_skus, item, space):
    '''DEPRECIATED NO NEED TO USE I THINK
    takes the num of skus of item in space needed and 
    returns a list of items if it\'s in the space, else error'''
    ############# !!!!!!!!!!!!!!!!! ####################
    # is this for all locations or only stores
    if (
        (type(item.current_location) == type(Warehouse.Warehouse_Master_List[0]))
        or
        (type(item.current_location) == type(Store.Store_Master_List[0]))
        ):
        # item is in warehouse right now
        item_code_wanted = item.item_code
        items_list = list()
        num_found = 0
        enough_found_flag = False
        for ind, val in enumerate(space.inventory_list):
            if val.item_code == item_code_wanted:
                num_found += 1
                items_list.append(val)
            if num_found >= num_of_skus:
                enough_found_flag = True
                break
        if enough_found_flag == False:
            raise ValueError(f"not enough {item.name} found in {space.name}")
        return items_list
    # maybe something for incoming_location
    # elif type(item.current_location) == \
    #                         type(Store.Store_Master_List[0]):
    #     raise NotImplementedError('what to do here')
    else:
        # either this is trans_co/incoming_location, or some weird other bug
        raise NotImplementedError('this shouldn\'t be called then')
        

def add_item_to_incoming(item):
    if item.current_location != None:
        # should i remove from location?
        raise ValueError('item should be new, i.e have location None')
    item.current_location = Trans_Co.instance.incoming_location
    Trans_Co.instance.incoming_location.inventory_list.append(item)
    
    
def add_item_to_transitioning(item):
    if item.current_location not in Warehouse.Master_List:
        # should i remove from location?
        raise ValueError('item should be new, i.e have location None')
    item.current_location = Trans_Co.instance.transitioning_location
    Trans_Co.instance.transitioning_location.inventory_list.append(item)    

'''
HERE LIES WHAT USED TO BE INTER_OBJECT_FUNCTIONS
'''
def Calculate_Space_Total_Holding():    
    #ensure that all objects are .update()ed before calling this
    for space in Space.Master_List: #Space is the name of the Class of which space is an instance
        daily_total_holding_cost = float(0)
        for item in space.inventory_list:
            daily_total_holding_cost += float(item.daily_holding_cost)
        space.total_daily_holding_cost_list[Simulator.instance.day] = daily_total_holding_cost
    # print('Metrics Calculated and updated to space.total_daily_holding_cost_list')
    
def Store_Total_Sales():
    '''
    buy_list = list() # should be received or in or a slice of store.buy_list etc
    get_master_lists()
    for store in _List:
        space.daily_total_sales = float(0)
        for item in buy_list:
            space.daily_total_sales += float(item.daily_holding_cost)
    '''
    return 0

def Space_Total_Cost():
    ''' If we want to add in another KPI then we can
    or we could count the cost of the sold items separately
    and the items still in stock separate - deadstock?'''
    return 0

def init_store_quantity():
    '''this one just makes the warehouse have more than a 1000 quantity of any item needed'''
    for space in Space.Master_List:
        warehouse = space
        for item_code_key in warehouse.sku_stock_tally:
            num_skus = warehouse.sku_stock_tally[item_code_key]
            recent_item = Item.get_first_item_from_code(item_code_key, 
                                                        warehouse.inventory_list)
            quantity = (
                recent_item.sku_quantity * num_skus
                - recent_item.sku_quantity
                + recent_item.quantity
            )
            
            desired_quantity = 1000
            diff = desired_quantity - quantity
            skus_needed = ceil(diff/recent_item.sku_quantity)
            if skus_needed <= 0:
                print(f"skus_needed {skus_needed} is 0 or less for item_code {item_code_key}")
            spawn_list = [recent_item.spawn_new_copy() for _ in range(skus_needed)]
            add_item_skus_in_list_to_space(spawn_list, Warehouse.Warehouse_Master_List[0])
    pass

def init_warehouse_max_stock():
    '''this one just makes the warehouse have more than a 1000 quantity of all items in Item.codes_list'''
    for space in Warehouse.Warehouse_Master_List:
        warehouse = space
        for item_code_key in Item.codes_list:
            if item_code_key in warehouse.sku_stock_tally:
                num_skus = warehouse.sku_stock_tally[item_code_key]
            else:
                num_skus = 0
            recent_item = Item.get_first_item_from_code(item_code_key, 
                                                        Item.Master_List)
            quantity = (
                recent_item.sku_quantity * (num_skus - 1)
                + recent_item.quantity
            )
            if num_skus <= 0:
                quantity = 0 
            
            desired_quantity = 400
            diff = desired_quantity - quantity
            skus_needed = ceil(diff/recent_item.sku_quantity)
            if skus_needed <= 0:
                continue
            spawn_list = [recent_item.spawn_new_copy() for _ in range(skus_needed)]
            add_item_skus_in_list_to_space(spawn_list, Warehouse.Warehouse_Master_List[0])

    pass

def get_item_code_quantity_in_list(item_code, lis):
    '''ideally this should be replaced with a dictionary'''
    quantity = sum([item.quantity for item in lis if item.item_code == item_code])
    return quantity

def init_max_stock():
    '''every item code in Item.codes_list is added to every location upto it's max stock level'''
    for space in Space.Master_List:
        for item_code_key in Item.codes_list:
            lis = space.inventory_list
            # quantity = get_item_code_quantity_in_list(item_code_key, lis)
            quantity = 0
            desired_quantity = Plan.get_max_item_quantity_levels(item_code_key, space)
            new_skus = []
            temp_item = Item.get_first_item_from_code(item_code_key, Item.Master_List)
            while desired_quantity > quantity:
                it = (Item.spawn_copy(temp_item))
                new_skus.append(it)
                quantity += it.quantity
            # add to stock tally
            add_item_skus_in_list_to_space(new_skus, space)

    for item in Item.Master_List:
        if item.current_location == None:
            Item.Master_List.remove(item)

def init_low_stock():
    '''every item code in Item.codes_list is added to every location upto it's max stock level'''
    for warehouse in Warehouse.Warehouse_Master_List:
        space = warehouse
        for item_code_key in Item.codes_list:
            lis = space.inventory_list
            # quantity = get_item_code_quantity_in_list(item_code_key, lis)
            quantity = 0
            desired_quantity = Plan.get_max_item_quantity_levels(item_code_key, space)
            new_skus = []
            temp_item = Item.get_first_item_from_code(item_code_key, Item.Master_List)
            while desired_quantity > quantity:
                it = (Item.spawn_copy(temp_item))
                new_skus.append(it)
                quantity += it.quantity
            # add to stock tally
            add_item_skus_in_list_to_space(new_skus, space)

    for store in Store.Store_Master_List:
        space = store
        for item_code_key in Item.codes_list:
            lis = space.inventory_list
            # quantity = get_item_code_quantity_in_list(item_code_key, lis)
            quantity = 0
            desired_quantity = 1
            new_skus = []
            temp_item = Item.get_first_item_from_code(item_code_key, Item.Master_List)
            while desired_quantity > quantity:
                it = (Item.spawn_copy(temp_item))
                new_skus.append(it)
                quantity += it.quantity
            # add to stock tally
            add_item_skus_in_list_to_space(new_skus, space)
    
    for item in Item.Master_List:
        if item.current_location == None:
            Item.Master_List.remove(item)            

def init_predicted_supply():
    for space in Space.Master_List:
        for item_code_key in Item.codes_list:
            lis = space.inventory_list
            # quantity = get_item_code_quantity_in_list(item_code_key, lis)
            quantity = 0
            desired_quantity = Plan.get_max_item_quantity_levels(item_code_key, space)
            new_skus = []
            temp_item = Item.get_first_item_from_code(item_code_key, Item.Master_List)
            while desired_quantity > quantity:
                it = (Item.spawn_copy(temp_item))
                new_skus.append(it)
                quantity += it.quantity
            # add to stock tally
            add_item_skus_in_list_to_space(new_skus, space)

    for item in Item.Master_List:
        if item.current_location == None:
            Item.Master_List.remove(item)

forecast_filename = r".\data\forecast.csv"
forecast_file = pd.read_csv(forecast_filename)

def get_sales_from_df(item_code, store_num):
    Y = forecast_file.where(forecast_file.item == item_code)
    Z = Y.where(Y.store == store_num)
    Z = Z.dropna()
    sales_df = Z["predicted sales"]
    sales_list = list(sales_df)
    return sales_list

def get_forecasted_shipments(store, item_code):
    # ans_lis = [(day, item_code, num_of_skus)]
    demand_time_list = get_sales_from_df(item_code,store.id[1])
    template_item = Item.get_first_item_from_code(item_code)
 
    min_level = Plan.get_min_item_quantity_levels(item_code, store)
    max_level = Plan.get_max_item_quantity_levels(item_code, store)
    init_level = max_level
    curr_level = get_item_code_quantity_in_list(item_code, store.inventory_list)

    received_lis = [] # (day, store, item_code, num_skus)
    day_num = 0
    while day_num < 90:
        curr_level -= demand_time_list[day_num]
        if curr_level <= min_level:
            diff_qtty = max_level - curr_level
            num_skus = ceil(diff_qtty / template_item.sku_quantity)
            
            curr_level += num_skus*template_item.sku_quantity

            received_lis.append( 
                (day_num, store, item_code, num_skus)
            )
            # place this order, or append order to the order time list
            # !!!!!####!!!! NOTE THE TIME DELAY, NEED TO BACK CALCULATE BASED ON TRAVELING DELAY
        day_num += 1
    
    return received_lis

def draw_qnty_bar_chart(show_flag = False, save_flag = False):
    rows, cols = 3, 4
    left, right, bottom, top = 0, cols, 0, rows
    seqnc = [(row,col) for col in range(left, right) for row in range(bottom, top)]
    length = 50
    plt.style.use('seaborn-darkgrid')
    plt.rcParams["figure.figsize"] = (16,9)
    colours_index = "bgrcmyk"
    colour_list = [colours_index[ii % (len(colours_index))] for ii in range(length)]

    figs, axes = plt.subplots(rows, cols, 
                                sharex='col')
    for ind, space in enumerate(Space.Master_List):
        lis = space.inventory_list
        sku_stock_dict = space.sku_stock_tally
        quantity_stock_dict = {it_code : get_item_code_quantity_in_list(it_code, lis) 
                                for it_code in sku_stock_dict.keys()}
        axes[seqnc[ind]].bar(quantity_stock_dict.keys(), quantity_stock_dict.values(), color = colour_list)
        axes[seqnc[ind]].set_title(str(space.name))

    plt.tight_layout()
    if show_flag == True:
        plt.show(block=False)
    if save_flag == True:
        name = '.\images\overall_qnty_ ' + str(Simulator.instance.day)
        plt.savefig(name)
    plt.close()

def draw_histogram(show_flag = False, save_flag = False):
    rows, cols = 3, 4
    left, right, bottom, top = 0, cols, 0, rows
    seqnc = [(row,col) for col in range(left, right) for row in range(bottom, top)]
    length = 50
    plt.style.use('seaborn-darkgrid')
    plt.rcParams["figure.figsize"] = (16,9)
    colours_index = "bgrcmyk"
    colour_list = [colours_index[ii % (len(colours_index))] for ii in range(length)]

    figs, axes = plt.subplots(rows, cols, 
                                sharex='col')
    # for ind, (r,c) in enumerate(seqnc):
    #     rand_dict = {ii:randint(100,500) for ii in range(50)}
    #     axes[seqnc[ind]].bar(rand_dict.keys(), rand_dict.values(), color = colour_list)
    
    for ind, space in enumerate(Space.Master_List):
        y_lis = space.total_daily_holding_cost_list
        x_lis = [ii for ii in range(len(space.total_daily_holding_cost_list))]
        
        axes[seqnc[ind]].plot(x_lis, y_lis, 'g')
        axes[seqnc[ind]].set_title(str(space.name))

    plt.tight_layout()
    if show_flag == True:
        plt.show(block=False)
    if save_flag == True:
        name = '.\images\overall_holding_ ' + str(Simulator.instance.day)
        plt.savefig(name)
    plt.close()
