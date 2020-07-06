from haversine import haversine, Unit
import numpy as np
import pandas as pd
import xlrd
import xlwt

# Loading the data
data = pd.read_excel('Data Excercise 2 - EMTE stores - BA 2020-1.xlsx')


class Vrp:
    def __init__(self, data_frame):
        self.data = data_frame
        self.dm = pd.DataFrame()  # Distance matrix
        self.max_worked_minutes = 660  # i.e. 11 hours
        self.closing_time = 1020  # i.e. 17.00 pm / closing time
        self.route_nr = 1  # Start at route nr. 1
        self.route = pd.DataFrame({'Route Nr.': [1], 'City Nr.': [0], 'City Name': ['EMTE HEADQUARTERS VEGHEL'],
                                   'Total Distance in Route (km)': [0], 'Visit Time': [np.nan],
                                   'Distance from Previous': [0], 'Driving Time from Previous': [0],
                                   'Total Distance (km)': [0]})

    def distance_matrix(self):
        for i in self.data['City Nr.']:
            dist_list = [round(haversine((self.data['Lat'][i], self.data['Long'][i]),
                                         (self.data['Lat'][j], self.data['Long'][j])), 0) for j in self.data['City Nr.']]
            self.dm[i] = dist_list

    def add_visit_times(self):
        visit_times = [30 if self.data['Type'][i] == 'Jumbo' else 20 for i in self.data['City Nr.']]
        visit_times[0] = np.nan
        self.data['Visit Time'] = visit_times

    def check_constraints(self):
        """
        We check two constraints. John cannot work more than 11 hours (660 minutes) and John should finish each visit
        before the closing time of the store (and after the opening time). It is assumed that John is always present at
        the first store at 9 am (540 minutes after midnight).
        :return: True/False
        """
        current_route = self.route[self.route['Route Nr.'] == self.route_nr]  # Subset of current route
        total_driving_time = current_route['Driving Time from Previous'].sum()  # In minutes
        total_visit_times = current_route['Visit Time'].sum()
        current_store = current_route['City Nr.'][len(self.route)-1]
        driving_time_back = round(self.dm[current_store][0] / 1.5, 0)
        minutes_worked = total_driving_time + total_visit_times + driving_time_back
        if minutes_worked > self.max_worked_minutes:
            return False
        # We skip the driving time from hq to first store, since this can be done before 9 am.
        current_route_indexes = list(current_route.index.values)
        time_after_visit = 540 + total_visit_times + total_driving_time - \
                           current_route['Driving Time from Previous'][current_route_indexes[1]]
        if time_after_visit > self.closing_time:
            return False
        return True

    def one_route(self):
        current_store = 0
        while True:
            dist = self.dm[current_store].copy(deep=True)  # Take distances of current store (column)
            if current_store == 0:  # Only necessary for first store, after its already deleted from distance matrix
                dist.drop(current_store, inplace=True)  # Drop the current store, distance is always 0
            else:  # HQ is removed, unless it is the first store in the route
                dist.drop(0, inplace=True)
            if len(dist) == 0:  # If after dropping HQ dist is empty, we have reached the last store and should break
                new_last_store = self.route['City Nr.'][len(self.route) - 1]
                distance_to_hq = self.dm[new_last_store][0]  # Distance from last visited store to hq
                total_route_distance = self.route['Total Distance in Route (km)'][len(self.route) - 1] + distance_to_hq
                total_distance = self.route['Total Distance (km)'][len(self.route) - 1] + distance_to_hq
                self.route = self.route.append({'Route Nr.': self.route_nr, 'City Nr.': 0,
                                                'City Name': 'EMTE HEADQUARTERS VEGHEL',
                                                'Total Distance in Route (km)': total_route_distance,
                                                'Visit Time': np.nan,
                                                'Distance from Previous': distance_to_hq,
                                                'Driving Time from Previous': round((distance_to_hq / 1.5), 0),
                                                'Total Distance (km)': total_distance},
                                               ignore_index=True)  # Add hq to route
                return False
            shortest_distance = dist.min()
            closest_store = dist.idxmin()  # Returns index (store) of lowest distance
            store_name = self.data['Name'][closest_store]  # Retrieve name of store from data frame
            total_route_distance = self.route['Total Distance in Route (km)'][len(self.route) - 1] + shortest_distance
            total_distance = self.route['Total Distance (km)'][len(self.route) - 1] + shortest_distance
            self.route = self.route.append({'Route Nr.': self.route_nr, 'City Nr.': closest_store,
                                            'City Name': store_name,
                                            'Total Distance in Route (km)': total_route_distance,
                                            'Visit Time': self.data['Visit Time'][closest_store],
                                            'Distance from Previous': shortest_distance,
                                            'Driving Time from Previous': round((shortest_distance / 1.5), 0),
                                            'Total Distance (km)': total_distance},
                                           ignore_index=True)
            if self.check_constraints():  # Accept the new route and continue
                self.dm.drop(closest_store, inplace=True)  # remove the closest store from the distance matrix
                current_store = closest_store  # Change the current store for next iteration
            else:
                self.route.drop(len(self.route) - 1, inplace=True)  # Drop the last store
                new_last_store = self.route['City Nr.'][len(self.route) - 1]
                distance_to_hq = self.dm[new_last_store][0]  # Distance from last visited store to hq
                total_route_distance = self.route['Total Distance in Route (km)'][len(self.route) - 1] + distance_to_hq
                total_distance = self.route['Total Distance (km)'][len(self.route) - 1] + distance_to_hq
                self.route = self.route.append({'Route Nr.': self.route_nr, 'City Nr.': 0,
                                                'City Name': 'EMTE HEADQUARTERS VEGHEL',
                                                'Total Distance in Route (km)': total_route_distance,
                                                'Visit Time': np.nan,
                                                'Distance from Previous': distance_to_hq,
                                                'Driving Time from Previous': round((distance_to_hq / 1.5), 0),
                                                'Total Distance (km)': total_distance},
                                               ignore_index=True)  # Add hq to route
                break
        self.route_nr += 1
        return True

    def all_routes(self):
        while True:
            if self.route_nr > 1:  # Start a new route by adding hq (unless it is the first route)
                self.route = self.route.append({'Route Nr.': self.route_nr, 'City Nr.': 0,
                                                'City Name': 'EMTE HEADQUARTERS VEGHEL',
                                                'Total Distance in Route (km)': 0, 'Visit Time': np.nan,
                                                'Distance from Previous': 0, 'Driving Time from Previous': 0,
                                                'Total Distance (km)':
                                                    self.route['Total Distance (km)'][len(self.route) - 1]},
                                               ignore_index=True)
            if not self.one_route():
                break

    def output_route(self):
        output_df = self.route.copy(deep=True)
        output_df.drop(['Visit Time', 'Distance from Previous', 'Driving Time from Previous'], axis=1, inplace=True)
        return output_df


john = Vrp(data_frame=data)  # Initialize object
john.distance_matrix()  # Create distance matrix
john.add_visit_times()  # Add the visit times for each store to original data
john.all_routes()  # Plan the routes
output = john.output_route()
output.to_excel("Ex2.1-1274850.xls", index=False)  # Save as excel file
print(f"Total amount of days needed: {john.route_nr}")
