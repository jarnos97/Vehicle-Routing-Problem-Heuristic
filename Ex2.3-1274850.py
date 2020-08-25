from haversine import haversine, Unit
import numpy as np
import pandas as pd
import random
import xlrd
import xlwt
import math
import time
import random

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
        self.tabu_list = []
        self.swap_stores = None
        self.best_solution = None
        self.best_distance = math.inf  # So that the first new distance is always smaller
        self.no_improvement_counter = 0
        self.previous_total_distance = None

    def reset_variables(self, method):
        """
        This function resets the variables shared by tabu search and simulated annealing, so that they can be
        sequentially ran without causing problems.
        """
        if method == 'simulated_annealing':
            self.best_solution = None
            self.best_distance = math.inf
            self.previous_total_distance = -1  # This is different for tabu search
            self.dm = pd.DataFrame()  # Distance matrix
            self.distance_matrix()  # Re-initialize the distance matrix
        elif method == 'tabu_search':
            self.best_solution = None
            self.best_distance = math.inf
            self.previous_total_distance = math.inf
            self.dm = pd.DataFrame()  # Distance matrix
            self.distance_matrix()  # Re-initialize the distance matrix

    def distance_matrix(self):
        """
        Function loops over all stores, calculates for each store the distance to every other store and saves the result
        in a data frame.
        """
        for i in self.data['City Nr.']:
            dist_list = [round(haversine((self.data['Lat'][i], self.data['Long'][i]),
                                         (self.data['Lat'][j], self.data['Long'][j])), 0) for j in self.data['City Nr.']]
            self.dm[i] = dist_list

    def add_visit_times(self):
        """
        Function loops over the data and for each store gathers the store visit time based on store type, the result is
        added as a column to the data frame.
        """
        visit_times = [30 if self.data['Type'][i] == 'Jumbo' else 20 for i in self.data['City Nr.']]
        visit_times[0] = np.nan
        self.data['Visit Time'] = visit_times

    def check_constraints(self, other_route=None, route_number=None):
        """
        We check two constraints. John cannot work more than 11 hours (660 minutes) and John should finish each visit
        before the closing time of the store (and after the opening time). It is assumed that John is always present at
        the first store at 9 am (540 minutes after midnight). The functions' default is used for the initial route, the
        user can also specify a specific route, this is used for tabu search and simulated annealing.
        :return: True/False
        """
        if route_number:  # This is used for the tabu search and simulated annealing
            current_route = other_route[other_route['Route Nr.'] == route_number]  # Subset of current route
            total_driving_time = current_route['Driving Time from Previous'].sum()  # In minutes
            total_visit_times = current_route['Visit Time'].sum()
            if (total_driving_time + total_visit_times) > self.max_worked_minutes:  # Constraint 1: time worked
                return False
            route_indexes = list(current_route.index.values)
            time_after_visit = 540 + total_visit_times + total_driving_time - \
                               current_route['Driving Time from Previous'][route_indexes[1]] - \
                               current_route['Driving Time from Previous'][route_indexes[len(route_indexes)-1]]
            if time_after_visit > self.closing_time:  # Constraint 2: visiting time
                return False
            return True
        else:  # Used for the initial route
            current_route = self.route[self.route['Route Nr.'] == self.route_nr]  # Subset of current route
            total_driving_time = current_route['Driving Time from Previous'].sum()  # In minutes
            total_visit_times = current_route['Visit Time'].sum()
            current_store = current_route['City Nr.'][len(self.route)-1]
            driving_time_back = round(self.dm[current_store][0] / 1.5, 0)
            minutes_worked = total_driving_time + total_visit_times + driving_time_back
            if minutes_worked > self.max_worked_minutes:  # Constraint 1: time worked
                return False
            current_route_indexes = list(current_route.index.values)
            time_after_visit = 540 + total_visit_times + total_driving_time - \
                               current_route['Driving Time from Previous'][current_route_indexes[1]]
            if time_after_visit > self.closing_time:  # Constraint 2: visiting time
                return False
            return True

    def one_route(self):
        """
        The function uses the nearest neighbor insertion method to select new stores to append to the route. The closest
        store (from previous) is temporarily added to the data frame, which is then checked to assess feasibility.
        If the constraints are met, the new route is accepted, otherwise the route is restored to its previous state.
        The function stops when no feasible route is found or if the final store was added to the route.
        :return: True/False
        """
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
            total_route_distance = self.route['Total Distance in Route (km)'][len(self.route) - 1] + shortest_distance
            total_distance = self.route['Total Distance (km)'][len(self.route) - 1] + shortest_distance
            self.route = self.route.append({'Route Nr.': self.route_nr, 'City Nr.': closest_store,
                                            'City Name': self.data['Name'][closest_store],
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
        """
        The function sequentially runs the one_route() method and adds routes to the data frame, the function terminates
        when one_route() returns false.
        """
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

    def output_route(self, manual_route=None):
        """
        Function drops unnecessary columns to obtain desired output.
        :param manual_route:
        :return: data frame
        """
        if manual_route is not None:
            output_df = manual_route.copy(deep=True)
        else:
            output_df = self.route.copy(deep=True)
        output_df.drop(['Visit Time', 'Distance from Previous', 'Driving Time from Previous'], axis=1, inplace=True)
        return output_df

    def swap(self, temp_route):
        """
        Function randomly select two stores and swaps them.
        """
        self.swap_stores = list(np.random.choice(range(1, 134), 2, replace=False))  # Select stores to swap
        s1_index = temp_route.index[temp_route['City Nr.'] == self.swap_stores[0]][0]  # Index of store 1
        s2_index = temp_route.index[temp_route['City Nr.'] == self.swap_stores[1]][0]  # Index of store 2
        s1 = pd.DataFrame(dict(temp_route.iloc[s1_index]), index=[s2_index])  # Create dataframe of store
        s2 = pd.DataFrame(dict(temp_route.iloc[s2_index]), index=[s1_index])  # Use opposite index
        s1_route_nr = int(s1['Route Nr.'])  # We switch the route number so its easier to slice the data later
        s2_route_nr = int(s2['Route Nr.'])
        s1['Route Nr.'] = s2_route_nr
        s2['Route Nr.'] = s1_route_nr
        temp_route.drop([s1_index], axis=0, inplace=True)  # Drop them from the route
        temp_route.drop([s2_index], axis=0, inplace=True)
        temp_route = temp_route.append(s1, ignore_index=False)  # Apply the swap
        temp_route = temp_route.append(s2, ignore_index=False)
        temp_route.sort_index(inplace=True)  # Places stores at correct index
        return temp_route, s1_route_nr, s2_route_nr, s1_index, s2_index

    def update_route_part(self, temp_route, route_nr_1, s1_index):
        """
        Function Takes the adapted route, from swap() and updates the distances and travel times in the altered route
        numbers. This approach is not very elegant in code (many lines), yet is computationally much more efficient than
        looping over the data frame and updating it.
        """
        route_index_range = temp_route.index[temp_route['Route Nr.'] == route_nr_1]  # All indexes of store 1
        r1_begin, r1_end = s1_index, route_index_range[len(route_index_range) - 1]  # Alter these indexes
        # Create the columns/lists we already know
        route_nrs = [route_nr_1] * len(route_index_range)
        city_nrs = temp_route['City Nr.'][r1_begin:r1_end + 1].to_list()
        city_names = temp_route['City Name'][r1_begin:r1_end + 1].to_list()
        visit_times = temp_route['Visit Time'][r1_begin:r1_end + 1].to_list()
        # Initialize new lists
        total_distance_in_route, distance_from_previous, driving_time_from_previous, total_distance = ([] for i in
                                                                                                       range(4))
        previous_store = temp_route['City Nr.'][r1_begin - 1]
        route_distance_previous = temp_route['Total Distance in Route (km)'][r1_begin - 1]
        total_distance_previous = temp_route['Total Distance (km)'][r1_begin - 1]
        for store in city_nrs:
            dist = self.dm[previous_store][store]
            distance_from_previous.append(dist)
            driving_time_from_previous.append(round((dist / 1.5), 0))
            total_distance_in_route.append(route_distance_previous + dist)
            total_distance.append(total_distance_previous + dist)
            previous_store = store
            route_distance_previous += dist
            total_distance_previous += dist
        route_part = pd.DataFrame(zip(route_nrs, city_nrs, city_names, total_distance_in_route, visit_times,
                                      distance_from_previous, driving_time_from_previous, total_distance),
                                  columns=['Route Nr.', 'City Nr.', 'City Name', 'Total Distance in Route (km)',
                                           'Visit Time', 'Distance from Previous', 'Driving Time from Previous',
                                           'Total Distance (km)'], index=list(np.arange(r1_begin, r1_end + 1, 1)))
        return route_part, list(np.arange(r1_begin, r1_end + 1, 1))

    @staticmethod
    def update_route(temp_route, new_route_1, new_route_2, index_range_1, index_range_2):
        """
        Function takes the temporary route and the two new routes created by update_route_part() and their indexes and
        replaces the stores in the temporary route with the new ones.
        :param temp_route: new_route_1: new_route_2: index_range_1: index_range_2:
        :return: data frame
        """
        if new_route_1['Route Nr.'].iloc[0] != new_route_2['Route Nr.'].iloc[0]:  # If within route swap dont drop again
            temp_route.drop(index_range_2, axis=0, inplace=True)
            temp_route = temp_route.append(new_route_2, ignore_index=False)
        temp_route.drop(index_range_1, axis=0, inplace=True)  # Drop the old rows from the route
        temp_route = temp_route.append(new_route_1, ignore_index=False)  # Append new rows
        temp_route.sort_index(inplace=True)  # Place rows at correct index
        previous_distances = temp_route['Distance from Previous'].to_list()  # Update the total distance for route
        total_distances = []
        total = 0
        for i in previous_distances:
            total += i
            total_distances.append(total)
        temp_route['Total Distance (km)'] = total_distances
        return temp_route

    def tabu_search(self):
        """
        The function applies a swap of two stores and updates the route. It then checks the feasibility of the new
        temporary route. If the total distance in the temporary route is less than 20 km worse than the previous and
        the swap is not yet is the tabu-list, it is accepted. Swaps that lead to improvement are always accepted. The
        function keeps track of the best solution and terminates after a given time limit or if there is no improvement
        for 100 steps.
        Note: I implemented the extra condition that a swap is not applied if the total distance is more than 20 km
        worse than the previous total distance (as mentioned in the discussion).
        """
        start_time = time.perf_counter()
        self.reset_variables(method='tabu_search')
        while (time.perf_counter() - start_time) < 1000:
            # Apply swap and update route
            temp_route = self.route.copy(deep=True)  # Makes copy of current route object
            temp_route, r_n_1, r_n_2, idx_1, idx_2 = self.swap(temp_route)  # Perform one swap
            new_route_1, index_range_1 = self.update_route_part(temp_route, r_n_1, idx_1)  # Update route one and two
            new_route_2, index_range_2 = self.update_route_part(temp_route, r_n_2, idx_2)
            temp_route = self.update_route(temp_route, new_route_1, new_route_2, index_range_1, index_range_2)
            # Checking the requirements for a swap: constraints, improvement, tabu_list, no improvement counter
            if not self.check_constraints(other_route=temp_route, route_number=r_n_1):  # Check constraints
                continue
            elif not self.check_constraints(new_route_2, r_n_2):
                continue
            if (temp_route['Total Distance (km)'][len(temp_route)-1] - self.previous_total_distance) > 20:
                continue
            if temp_route['Total Distance (km)'][len(temp_route)-1] > self.previous_total_distance:
                if self.swap_stores in self.tabu_list:  # Check if the stores to be swapped are in the Tabu list
                    continue
                self.swap_stores.reverse()
                if self.swap_stores in self.tabu_list:  # And check the reverse order
                    continue
                self.no_improvement_counter += 1
            else:
                self.no_improvement_counter = 0
            if self.no_improvement_counter >= 100:  # check second exit condition
                break
            # Accepting swap as new route
            self.swap_stores.reverse()  # Back to original
            self.route = temp_route.copy(deep=True)  # If constraints met, replace self.route with temp_route
            if len(self.tabu_list) == 50:  # If tabu list is full, remove first (oldest) entry
                self.tabu_list.pop(0)
            self.tabu_list.append(self.swap_stores)  # Append latest swap
            if self.route['Total Distance (km)'][len(self.route)-1] < self.best_distance:  # The total distance in route
                self.best_distance = self.route['Total Distance (km)'][len(self.route)-1]  # Save new best distance
                self.best_solution = self.route.copy(deep=True)  # Save new best route
            self.previous_total_distance = self.route['Total Distance (km)'][len(self.route)-1]  # Update variable
        return self.best_distance, self.best_solution

    def simulated_annealing(self):
        """
        The function applies a swap of two stores and updates the route. It then checks the feasibility of the new
        temporary route. If there is an improvement (negative Delta), the swap is accepted. Otherwise, it is accepted
        with some probability. After each swap, the temperature is adapted according to the cooling-down-rate. The
        function keeps track of the best solution and terminates after a given time limit or the temperature limit is
        reached.
        Note: I implemented the extra condition from tabu-search here again. However, this did not yield better results.
        Therefore, I have removed it again.
        """
        start_time = time.perf_counter()
        self.reset_variables(method='simulated_annealing')  # Initialize necessary variables
        temperature = 1000
        cooling = 0.999
        while (time.perf_counter() - start_time) < 1000:
            # Apply swap and update route
            temp_route = self.route.copy(deep=True)  # Makes copy of current route object
            temp_route, r_n_1, r_n_2, idx_1, idx_2 = self.swap(temp_route)  # Perform one swap
            new_route_1, index_range_1 = self.update_route_part(temp_route, r_n_1, idx_1)  # Update route one and two
            new_route_2, index_range_2 = self.update_route_part(temp_route, r_n_2, idx_2)
            temp_route = self.update_route(temp_route, new_route_1, new_route_2, index_range_1, index_range_2)
            if not self.check_constraints(other_route=temp_route, route_number=r_n_1):  # Check constraints
                continue
            elif not self.check_constraints(new_route_2, r_n_2):
                continue
            delta = temp_route['Total Distance (km)'][len(temp_route)-1] - self.previous_total_distance
            if delta >= 0:  # IF there is no improvement
                prob = math.exp((delta * -1) / temperature)
                if random.random() > prob:
                    continue
            # Accepting swap as new route
            self.route = temp_route.copy(deep=True)  # If constraints met, replace self.route with temp_route
            if self.route['Total Distance (km)'][len(self.route)-1] < self.best_distance:  # The total distance in route
                self.best_distance = self.route['Total Distance (km)'][len(self.route)-1]  # Save new best distance
                self.best_solution = self.route.copy(deep=True)  # Save new best route
            self.previous_total_distance = self.route['Total Distance (km)'][len(self.route)-1]  # Update variable
            temperature *= cooling  # Update temperature
            if temperature < 0.001:  # check second exit condition
                break
        return self.best_distance, self.best_solution


# Creating initial route
john = Vrp(data_frame=data)  # Initialize object
john.distance_matrix()  # Create distance matrix
john.add_visit_times()  # Add the visit times for each store to original data
john.all_routes()  # Plan the routes

# Simulated Annealing
route_distance, route = john.simulated_annealing()
print(route_distance)
output = john.output_route(route)
output.to_excel("Ex2.3-1274850.xls", index=False)  # Save as excel file
