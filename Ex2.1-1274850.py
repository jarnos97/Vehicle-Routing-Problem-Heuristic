from haversine import haversine, Unit
import numpy as np
import pandas as pd
import xlrd

#%%
"""
Loading the data
"""
data = pd.read_excel('Data Excercise 2 - EMTE stores - BA 2020-1.xlsx')

"""
The rounding is a bit ambiguous. Do I round after adding each distance?
"""


#%%
class Vrp:
    def __init__(self, data_frame):
        self.data = data_frame
        self.dm = pd.DataFrame()
        self.route = pd.DataFrame({'Route Nr.': [1], 'City Nr.': [0], 'City Name': ['EMTE HEADQUARTERS VEGHEL'],
                                   'Total Distance in Route (km)': [0]})
        self.max_hours = 11
        self.closing_time = 17
        self.driving_speed = 90
        self.route_nr = 1
        self.current_time = 9
        # self.hq_coordinates = (51.607, 5.52805)

    def distance_matrix(self):
        for i in self.data['City Nr.']:
            dist_list = [haversine((self.data['Lat'][i], self.data['Long'][i]),
                                   (self.data['Lat'][j], self.data['Long'][j])) for j in self.data['City Nr.']]
            self.dm[i] = dist_list
        return self.dm  # TODO: Don't have to return it, but keep temporarily for insight

    def add_visit_times(self):
        visit_times = [30 if self.data['Type'][i] == 'Jumbo' else 20 for i in self.data['City Nr.']]
        visit_times[0] = np.nan
        self.data['Visit Time'] = visit_times
        return self.data  # TODO: Don't have to return it, but keep temporarily for insight

    @staticmethod
    def distance_per_store(temp_route):
        cumulative_distances = temp_route['Total Distance in Route (km)'].to_list()
        cumulative_distances.reverse()
        cumulative_distances_2 = cumulative_distances[1:]  # Copy every value except the first
        cumulative_distances.pop(len(cumulative_distances) - 1)  # Pop the last entry
        distance_per_store = [i - j for i, j in zip(cumulative_distances, cumulative_distances_2)]
        distance_per_store.reverse()
        distance_per_store.insert(0, 0)  # Since the first
        temp_route['Distance from Previous'] = distance_per_store
        return temp_route

    def check_constraints(self, temp_route):
        total_driving_time = temp_route['Total Distance in Route (km)'][len(temp_route)-1] / 1.5  # In minutes
        temp_route = self.distance_per_store(temp_route)
        print('hierna')  # Doesn't show
        print(temp_route)


        # Continue here --> see
        """
        2 constraints:
        - start & end at HQ
        - don't work more than 11 hours
    
        current_time_after_visit = 09.00 + sum(store_visit_times) + sum(driving times starting from the first store (hq 1 does not count)
        current_time_after_visit !> closing_time (17.00)
        start_time = 
        current_time - start_time !> 11 hours
        """


        total_visit_time = 3
        time_after_visit = 3
        return True

    def one_route(self):
        current_store = 0
        dist = pd.DataFrame(self.dm[current_store].to_list())  # Take distances of current store (column)
        dist.drop(current_store, inplace=True)  # Drop the current store, distance is always 0
        if current_store != 0:
            dist.drop(0, inplace=True)  # HQ is removed, unless it is the first store in the route
        shortest_distance = dist.min()
        closest_store = dist.idxmin()  # Returns index (store) of lowest distance
        store_name = self.data['Name'][closest_store[0]]  # Retrieve name of store from data frame
        total_route_distance = self.route['Total Distance in Route (km)'][len(self.route) - 1] + shortest_distance[0]
        temp_route = self.route.copy(deep=True)  # This temporary route is checked for constraints
        temp_route = temp_route.append({'Route Nr.': self.route_nr, 'City Nr.': closest_store[0],
                                        'City Name': store_name,
                                        'Total Distance in Route (km)': total_route_distance},
                                       ignore_index=True)
        if self.check_constraints(temp_route):   # Accept the new route and continue
            self.route = self.route.append({'Route Nr.': self.route_nr, 'City Nr.': closest_store[0],
                                            'City Name': store_name,
                                            'Total Distance in Route (km)': total_route_distance},
                                           ignore_index=True)  # Add store to route
            self.dm.drop(closest_store, inplace=True)  # remove the closest store from the distance matrix
            current_store = closest_store  # Change the current store for next iteration
        else:  # Add hq to end of route and break from loop
            last_store = self.route['City Nr.'][len(self.route)-1]
            distance_to_hq = self.dm[last_store][0]  # Distance from last visited store to hq
            print(distance_to_hq)
            total_route_distance = self.route['Total Distance in Route (km)'][len(self.route) - 1] + distance_to_hq
            self.route = self.route.append({'Route Nr.': self.route_nr, 'City Nr.': 0,
                                            'City Name': 'EMTE HEADQUARTERS VEGHEL',
                                            'Total Distance in Route (km)': total_route_distance},
                                           ignore_index=True)  # Add hq to route
            # break
        self.route_nr += 1
        return self.route


#%%
# Initialize object
john = Vrp(data_frame=data[:10])

#%%
# Create distance matrix
distances = john.distance_matrix()  # TODO: Remember to delete the variable assignment

#%%
# Add the visit times for each store to original data
data = john.add_visit_times()  # TODo: Remember to delete the variable assignment

#%%
route = john.one_route()
print(len(route))

#%%

