from haversine import haversine, Unit
import numpy as np
import pandas as pd
import xlrd

#%%
"""
Loading the data
"""
data = pd.read_excel('Data Excercise 2 - EMTE stores - BA 2020-1.xlsx')


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

    def check_constraints(self):
        pass

    def one_route(self):
        current_store = 0
        if self.route_nr == 1:  # In the first route the HQ is still present
            dist = pd.DataFrame(self.dm[current_store].to_list())  # Take distances of current store (column)
            dist.drop(current_store, inplace=True)  # Drop the current store, distance is always 0
            shortest_distance = dist.min()
            closest_store = dist.idxmin()  # Returns index (store) of lowest distance
            store_name = self.data['Name'][closest_store[0]]  # Retrieve name of store from data frame
            self.route = self.route.append({'Route Nr.': self.route_nr, 'City Nr.': closest_store[0],
                                            'City Name': store_name,
                                            'Total Distance in Route (km)': shortest_distance[0]}, ignore_index=True)
            if check_constraints():
                # Accept the new route and continue
                print('ja')
            else:
                # Remove the store from the route and end the current route --> add hq to end
                print('mh')
            return self.route
        else:
            # add hq back to distance matrix
            dist = pd.DataFrame(self.dm[current_store].to_list())  # Take distances of current store (column)
            dist.drop(current_store, inplace=True)  # Drop the current store, distance is always 0
            shortest_distance = dist.min()
            closest_store = dist.idxmin()  # Returns index (store) of lowest distance

            # Check constraints?

            self.route = self.route.append({'Route Nr.': self.route_nr, 'City Nr.': closest_store,
                                            'City Name': self.data['Name'][closest_store][0],
                                            'Total Distance in Route (km)': shortest_distance[0]}, ignore_index=True)
            return self.route

        # Always start from the headquarters
        # while True:
        # dist = pd.DataFrame(route_dm[current_store].to_list())
        # dist.drop(current_store, inplace=True)  # Drop the current store, distance is always 0
        shortest_distance = dist.min()
        closest_store = dist.idxmin()  # Returns index of lowest distance
        # route_dm.drop(current_store, axis=0, inplace=True)


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


