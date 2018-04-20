from aguaclara_research.play import *


def ftime(data_file_path, start, end=-1):
    """This function extracts the column of times from a ProCoDA data file.

    Parameters
    ----------
    data_file_path : string
        File path. If the file is in the working directory, then the file name
        is sufficient.

    start : int
        Index of first row of data to extract from the data file

    end : int, optional
        Index of last row of data to extract from the data
        Defaults to -1, which extracts all the data in the file

    Returns
    -------
    numpy array
        Experimental times starting at 0 day with units of days.

    Examples
    --------


    """
    df = pd.read_csv(data_file_path, delimiter='\t')
    start_time = pd.to_numeric(df.iloc[start, 0])*u.day
    day_times = pd.to_numeric(df.iloc[start:end, 0])
    time_data = np.subtract((np.array(day_times)*u.day), start_time)
    return time_data


def Column_of_data(data_file_path, start, end, column, units=""):
    """This function extracts a column of data from a ProCoDA data file.

    Parameters
    ----------
    data_file_path : string
        File path. If the file is in the working directory, then the file name
        is sufficient.

    start : int
        Index of first row of data to extract from the data file

    end : int
    Index of last row of data to extract from the data
    If the goal is to extract the data up to the end of the file use -1

    column : int
        Index of the column that you want to extract. Column 0 is time.
        The first data column is column 1.

    units : string, optional
        The units you want to apply to the data, e.g. 'mg/L'.
        Defaults to "" which indicates no units

    Returns
    -------
    numpy array
        Experimental data with the units applied.

    Examples
    --------

    """
    df = pd.read_csv(data_file_path, delimiter='\t')
    if units == "":
        data = np.array(pd.to_numeric(df.iloc[start:end, column]))
    else:
        data = np.array(pd.to_numeric(df.iloc[start:end, column]))*u(units)
    return data


def notes(data_file_path):
    """This function extracts any experimental notes from a ProCoDA data file.

    Parameters
    ----------
    data_file_path : string
        File path. If the file is in the working directory, then the file name
        is sufficient.

    Returns
    -------
    dataframe
        The rows of the data file that contain text notes inserted during the
        experiment. Use this to identify the section of the data file that you
        want to extract.

    Examples
    --------

    """
    df = pd.read_csv(data_file_path, delimiter='\t')
    text_row = df.iloc[0:-1, 0].str.contains('[a-z]', '[A-Z]')
    text_row_index = text_row.index[text_row].tolist()
    notes = df.loc[text_row_index]
    return notes


def read_state(dates, state, column, units="", path=""):
    """Reads a ProCoDA file and outputs the data column and time vector for
    each iteration of the given state.

    Parameters
    ----------
    dates : string (list)
        A list of dates or single date for which data was recorded, in
        the form "M-D-Y"

    state : string
        The state ID number for which data should be extracted

    column : string
        Index of the column that you want to extract. Column 0 is time.
        The first data column is column 1.

    units : string, optional
        The units you want to apply to the data, e.g. 'mg/L'.
        Defaults to "" which indicates no units

    path : string, optional
        Optional argument of the path to the folder containing your ProCoDA
        files. Defaults to the current directory if no argument is passed in

    Returns
    -------
    time : numpy array
        Times corresponding to the data (with units)

    data : numpy array
        Data in the given column during the given state with units

    Examples
    --------
    time, data = read_state(["6-19-2013", "6-20-2013"], "1", 28, "mL/s")

    """
    data_agg = []
    day = 0
    first_day = True
    overnight = False

    if not isinstance(dates, list):
        dates = [dates]

    for d in dates:
        state_file = path + "statelog " + d + ".xls"
        data_file = path + "datalog " + d + ".xls"

        states = pd.read_csv(state_file, delimiter='\t')
        data = pd.read_csv(data_file, delimiter='\t')

        states = np.array(states)
        data = np.array(data)

        # get the start and end times for the state
        state_start_idx = states[:, 1] == state
        state_start = states[state_start_idx, 0]
        state_end_idx = np.append([False], state_start_idx[0:(np.size(state_start_idx)-1)])
        state_end = states[state_end_idx, 0]

        if overnight:
            state_start = np.insert(state_start, 0, 0)
            state_end = np.insert(state_end, 0, states[0, 0])

        if state_start_idx[-1]:
            state_end.append(data[0, -1])

        # get the corresponding indices in the data array
        data_start = []
        data_end = []
        for i in range(np.size(state_start)):
            add_start = True
            for j in range(np.size(data[:, 0])):
                if (data[j, 0] > state_start[i]) and add_start:
                    data_start.append(j)
                    add_start = False
                if (data[j, 0] > state_end[i]):
                    data_end.append(j-1)
                    break

        if first_day:
            start_time = data[1, 0]

        # extract data at those times
        for i in range(np.size(data_start)):
            t = data[data_start[i]:data_end[i], 0] + day - start_time
            c = data[data_start[i]:data_end[i], column]
            if overnight and i == 0:
                data_agg = np.insert(data_agg[-1], np.size(data_agg[-1][:, 0]),
                                     np.vstack((t, c)).T)
            else:
                data_agg.append(np.vstack((t, c)).T)

        day += 1
        if first_day:
            first_day = False
        if state_start_idx[-1]:
            overnight = True

    data_agg = np.vstack(data_agg)
    if units != "":
        return data_agg[:, 0]*u.day, data_agg[:, 1]*u(units)
    else:
        return data_agg[:, 0]*u.day, data_agg[:, 1]


def average_state(dates, state, column, units="", path=""):
    """Outputs the average value of the data for each instance of a state in
    the given ProCoDA files

    Parameters
    ----------
    dates : string (list)
        A list of dates or single date for which data was recorded, in
        the form "M-D-Y"

    state : string
        The state ID number for which data should be extracted

    column : string
        Index of the column that you want to extract. Column 0 is time.
        The first data column is column 1.

    units : string, optional
        The units you want to apply to the data, e.g. 'mg/L'.
        Defaults to "" which indicates no units

    path : string, optional
        Optional argument of the path to the folder containing your ProCoDA
        files. Defaults to the current directory if no argument is passed in

    Returns
    -------
    float list
        A list of averages for each instance of the given state

    Examples
    --------
    data_avgs = average_state(["6-19-2013", "6-20-2013"], "1", 28, "mL/s")

    """
    data_agg = []
    day = 0
    first_day = True
    overnight = False

    if not isinstance(dates, list):
        dates = [dates]

    for d in dates:
        state_file = path + "statelog " + d + ".xls"
        data_file = path + "datalog " + d + ".xls"

        states = pd.read_csv(state_file, delimiter='\t')
        data = pd.read_csv(data_file, delimiter='\t')

        states = np.array(states)
        data = np.array(data)

        # get the start and end times for the state
        state_start_idx = states[:, 1] == state
        state_start = states[state_start_idx, 0]
        state_end_idx = np.append([False], state_start_idx[0:(np.size(state_start_idx)-1)])
        state_end = states[state_end_idx, 0]

        if overnight:
            state_start = np.insert(state_start, 0, 0)
            state_end = np.insert(state_end, 0, states[0, 0])

        if state_start_idx[-1]:
            state_end.append(data[0, -1])

        # get the corresponding indices in the data array
        data_start = []
        data_end = []
        for i in range(np.size(state_start)):
            add_start = True
            for j in range(np.size(data[:, 0])):
                if (data[j, 0] > state_start[i]) and add_start:
                    data_start.append(j)
                    add_start = False
                if (data[j, 0] > state_end[i]):
                    data_end.append(j-1)
                    break

        if first_day:
            start_time = data[1, 0]

        # extract data at those times
        for i in range(np.size(data_start)):
            c = data[data_start[i]:data_end[i], column]
            if overnight and i == 0:
                data_agg = np.insert(data_agg[-1], np.size(data_agg[-1][:]), c)
            else:
                data_agg.append(c)

        day += 1
        if first_day:
            first_day = False
        if state_start_idx[-1]:
            overnight = True

    averages = np.zeros(np.size(data_agg))
    for i in range(np.size(data_agg)):
        averages[i] = np.average(data_agg[i])

    if units != "":
        return averages*u(units)
    else:
        return averages


def perform_function_on_state(func, dates, state, column, units="", path=""):
    """Performs the function given on each state of the data for the given state
    in the given column and outputs the result for each instance of the state

    Parameters
    ----------
    func : function
        A function which will be applied to data from each instance of the state

    dates : string (list)
        A list of dates or single date for which data was recorded, in
        the form "M-D-Y"

    state : string
        The state ID number for which data should be extracted

    column : string
        Index of the column that you want to extract. Column 0 is time.
        The first data column is column 1.

    units : string, optional
        The units you want to apply to the data, e.g. 'mg/L'.
        Defaults to "" which indicates no units

    path : string, optional
        Optional argument of the path to the folder containing your ProCoDA
        files. Defaults to the current directory if no argument is passed in

    Returns
    -------
    list
        The outputs of the given function for each instance of the given state

    Requires
    --------
    func takes in a list of data with units and outputs the correct units

    Examples
    --------
    def avg_with_units(lst):
        num = np.size(lst)
        acc = 0
        for i in lst:
            acc = i + acc

        return acc / num

    data_avgs = perform_function_on_state(avg_with_units, ["6-19-2013", "6-20-2013"], "1", 28, "mL/s")

    """
    data_agg = []
    day = 0
    first_day = True
    overnight = False

    if not isinstance(dates, list):
        dates = [dates]

    for d in dates:
        state_file = path + "statelog " + d + ".xls"
        data_file = path + "datalog " + d + ".xls"

        states = pd.read_csv(state_file, delimiter='\t')
        data = pd.read_csv(data_file, delimiter='\t')

        states = np.array(states)
        data = np.array(data)

        # get the start and end times for the state
        state_start_idx = states[:, 1] == state
        state_start = states[state_start_idx, 0]
        state_end_idx = np.append([False], state_start_idx[0:(np.size(state_start_idx)-1)])
        state_end = states[state_end_idx, 0]

        if overnight:
            state_start = np.insert(state_start, 0, 0)
            state_end = np.insert(state_end, 0, states[0, 0])

        if state_start_idx[-1]:
            state_end.append(data[0, -1])

        # get the corresponding indices in the data array
        data_start = []
        data_end = []
        for i in range(np.size(state_start)):
            add_start = True
            for j in range(np.size(data[:, 0])):
                if (data[j, 0] > state_start[i]) and add_start:
                    data_start.append(j)
                    add_start = False
                if (data[j, 0] > state_end[i]):
                    data_end.append(j-1)
                    break

        if first_day:
            start_time = data[1, 0]

        # extract data at those times
        for i in range(np.size(data_start)):
            c = data[data_start[i]:data_end[i], column]
            if overnight and i == 0:
                data_agg = np.insert(data_agg[-1], np.size(data_agg[-1][:]), c)
            else:
                data_agg.append(c)

        day += 1
        if first_day:
            first_day = False
        if state_start_idx[-1]:
            overnight = True

    output = np.zeros(np.size(data_agg))
    for i in range(np.size(data_agg)):
        if units != "":
            output[i] = func(data_agg[i]*u(units))
        else:
            output[i] = func(data_agg[i])

    return output


def plot_state(dates, state, column, path=""):
    """Reads a ProCoDA file and plots the data column for each iteration of
    the given state.

    Parameters
    ----------
    dates : string (list)
        A list of dates or single date for which data was recorded, in
        the form "M-D-Y"

    state : string
        The state ID number for which data should be plotted

    column : string
        Index of the column that you want to extract. Column 0 is time.
        The first data column is column 1.

    path : string, optional
        Optional argument of the path to the folder containing your ProCoDA
        files. Defaults to the current directory if no argument is passed in

    Returns
    -------
    None

    Examples
    --------
    plot_state(["6-19-2013", "6-20-2013"], "1", 28)

    """
    data_agg = []
    day = 0
    first_day = True
    overnight = False

    if not isinstance(dates, list):
        dates = [dates]

    for d in dates:
        state_file = path + "statelog " + d + ".xls"
        data_file = path + "datalog " + d + ".xls"

        states = pd.read_csv(state_file, delimiter='\t')
        data = pd.read_csv(data_file, delimiter='\t')

        states = np.array(states)
        data = np.array(data)

        # get the start and end times for the state
        state_start_idx = states[:, 1] == state
        state_start = states[state_start_idx, 0]
        state_end_idx = np.append([False], state_start_idx[0:(np.size(state_start_idx)-1)])
        state_end = states[state_end_idx, 0]

        if overnight:
            state_start = np.insert(state_start, 0, 0)
            state_end = np.insert(state_end, 0, states[0, 0])

        if state_start_idx[-1]:
            state_end.append(data[0, -1])

        # get the corresponding indices in the data array
        data_start = []
        data_end = []
        for i in range(np.size(state_start)):
            add_start = True
            for j in range(np.size(data[:, 0])):
                if (data[j, 0] > state_start[i]) and add_start:
                    data_start.append(j)
                    add_start = False
                if (data[j, 0] > state_end[i]):
                    data_end.append(j-1)
                    break

        if first_day:
            start_time = data[1, 0]

        # extract data at those times
        for i in range(np.size(data_start)):
            t = data[data_start[i]:data_end[i], 0] + day - start_time
            c = data[data_start[i]:data_end[i], column]
            if overnight and i == 0:
                data_agg = np.insert(data_agg[-1], np.size(data_agg[-1][:, 0]),
                                     np.vstack((t, c)).T)
            else:
                data_agg.append(np.vstack((t, c)).T)

        day += 1
        if first_day:
            first_day = False
        if state_start_idx[-1]:
            overnight = True

    plt.figure()
    for i in data_agg:
        t = i[:, 0] - i[0, 0]
        plt.plot(t, i[:, 1])

    plt.show()


def read_state_with_metafile(func, state, column, path, units=""):
    """Takes in a ProCoDA meta file and performs a function for all data of a
    certain state in each of the experiments (denoted by file paths in then
    metafile)

    Parameters
    ----------
    func : function
        A function which will be applied to data from each instance of the state

    state : string
        The state ID number for which data should be extracted

    column : string
        Index of the column that you want to extract. Column 0 is time.
        The first data column is column 1.

    path : string
        Path to your ProCoDA metafile (must be tab-delimited)

    units : string, optional
        The units you want to apply to the data, e.g. 'mg/L'.
        Defaults to "" which indicates no units

    Returns
    -------
    ids : string list
        The list of experiment ids given in the metafile

    outputs : list
        The outputs of the given function for each experiment

    Examples
    --------
    def avg_with_units(lst):
        num = np.size(lst)
        acc = 0
        for i in lst:
            acc = i + acc

        return acc / num

    read_state_with_metafile(avg_with_units, "")

    """
    outputs = []

    metafile = pd.read_csv(path, delimiter='\t', header=None)
    metafile = np.array(metafile)

    ids = metafile[1:, 0]

    basepath = metafile[0, 4]
    paths = metafile[1:-1, 4]

    # use a loop to evaluate each experiment in the metafile
    for i in range(paths):
        # get the range of dates for experiment i
        day1 = metafile[i+1, 1]

        # modify the metafile date so that it works with datetime format
        if day1[2] != "-":
            day1 = "0" + day1
        if day1[5] != "-":
            day1 = day1[:3] + "0" + day1[3:]

        dt = datetime.strptime(day1, "%m-%d-%Y")
        duration = metafile[i+1, 3]

        date_list = []
        for j in range(duration):
            curr_day = dt.strftime("%m-%d-%Y")
            if curr_day[3] == "0":
                curr_day = curr_day[:3] + curr_day[4:]
            if curr_day[0] == "0":
                curr_day = curr_day[1:]

            date_list.append(curr_day)

            dt = dt + timedelta(days=1)

        _, data = read_state(date_list, state, column, units, basepath + paths)

        outputs.append(func(data))

    return ids, outputs


def write_calculations_to_csv(funcs, states, columns, path, headers, out_name):
    """

    Parameters
    ----------
    funcs : function (list)
        A function or list of functions which will be applied in order to the
        data. If only one function is given it is applied to all the
        states/columns

    states : string (list)
        The state ID numbers for which data should be extracted. List should be
        in order of calculation or if only one state is given then it will be
        used for all the calculations

    columns : string (list)
        Index of the column that you want to extract. Column 0 is time.
        The first data column is column 1. If only one column is given it is
        used for all the calculations

    path : string
        Path to your ProCoDA metafile (must be tab-delimited)

    headers : string list
        List of the desired header for each calculation, in order

    out_name : string
        Desired name for the output file. Can include a relative path

    Returns
    -------
    out_name.csv
        A CSV file with the each column being a new calcuation and each row
        being a new experiment on which the calcuations were performed

    output : DataFrame
        Pandas dataframe which is the same data that was written to CSV

    Requires
    --------
    funcs, states, columns, and headers are all of the same length if they are
    lists. Some being lists and some single values are okay.

    Examples
    --------

    """
    if not isinstance(funcs, list):
        [funcs] * headers.len()

    if not isinstance(states, list):
        [states] * headers.len()

    if not isinstance(columns, list):
        [columns] * headers.len()

    data_agg = []
    for i in range(headers.len()):
        ids, data = read_state_with_metafile(funcs[i], states[i], columns[i], path)
        data_agg = np.append(data_agg, [data])

    output = pd.DataFrame(data=data_agg.T, columns=headers)
    output.to_csv(out_name, sep='\t')

    return output
