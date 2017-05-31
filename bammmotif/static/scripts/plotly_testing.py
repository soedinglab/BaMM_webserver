from plotly.offline import plot as plotly_plot
import plotly.graph_objs as go
import pandas as pd
import json

filename = "/home/kiesel/Desktop/BaMM_webserver/media/PlotlyTest/Output/wgEncodeOpenChromChipMcf7CtcfAlnRep0_summit_osMiQOZ_motif_1.scores"

data = {}
data['start'] = []
data['end'] = []
data['score'] = []
data['strand'] = []
data['pattern'] = []

with open ( filename ) as fh:
    for line in fh:
        head = list(line)
        if head[0] == ">":
            #header line
            print(line)
        else:
            tok = line.split ( ':' )
            # start - end - score - strand - pattern :
            data['start'].append(tok[0])
            data['end'].append ( tok[1] )
            data['score'].append ( tok[2] )
            data['strand'].append ( tok[3] )
            data['pattern'].append ( tok[4].strip() )


#trace1 = go.Scatter(x=data['start'] , y= data['score'],marker={'color': 'red', 'symbol': 104, 'size': "10"},
#                                mode="markers",  name='1st Trace')
trace1 = go.Histogram(x=data['start'], )
data=go.Data([trace1])
layout=go.Layout(title="", xaxis={'title':'Start Positions'}, yaxis={'title':'LogOddsScore'})
figure=go.Figure(data=data,layout=layout)
plotly_plot ( figure, auto_open=True)




def plot_convergence_trace_plotly(negll_trace_df, name, plot_title, plot_out=None):
    """
    Define a plot in plotly dictionary style
    Either plot it or return dictionary

    :param negll_trace_df:  Pandas Dataframe with columns: pass, step, $name
                            | pass | step | $name |
    :param name:            Column in negll_trace_df that is plotted as line
    :param plot_title:      title
    :param plot_out:        Path to HTML output file
    :return:
    """

    data = []
    for trace in name:
        for iteration in set(negll_trace_df['pass']):
            data.append(
                go.Scatter(
                    x=negll_trace_df[negll_trace_df['pass'] == iteration]['step'].tolist(),
                    y=negll_trace_df[negll_trace_df['pass'] == iteration][trace].tolist(),
                    mode='lines',
                    name=trace + ' pass ' + str(iteration),
                    connectgaps=True,
                    showlegend=False
                )
            )

    plot = {
        "data": data,
        "layout": go.Layout(
            title = plot_title,
            xaxis1 = dict(title="step",
                          exponentformat="e",
                          showexponent='All'),
            yaxis1 = dict(title=name,
                          exponentformat="e",
                          showexponent='All'
                          ),
            font = dict(size=18),
        )
    }

    if plot_out is not None:
        plotly_plot(plot, filename=plot_out, auto_open=False)
    else:
        return plot


def read_optimization_log_file(optimization_log_file):

    if not os.path.exists(optimization_log_file):
        print("Optimization log file {0} does not exist!".format(optimization_log_file))
        return  pd.DataFrame({})

    try:
        with open(optimization_log_file) as json_data:
            json_string = json.load(json_data)
    except Exception as e:
        print("Optimization log file {0} is not in json format!:{1}".format(optimization_log_file, e))
        return  pd.DataFrame({})

    log_df = pd.read_json(json_string, orient='split')
    return log_df

def main():
    parameters = "/home/kiesel/Desktop/Desktop/Plotly/parameters.log"
    log_df = read_optimization_log_file ( parameters )
    plot_convergence_trace_plotly ( log_df,
                                    name=['negLL', 'negLL_crossval'],
                                    plot_title='neg LL trace for training and cross-val set',
                                    plot_out='/home/kiesel/Desktop/Desktop/Plotly/Test.html')


########


with open ( score_file ) as fh:
    for line in fh:
        head = list(line)
        if head[0] == ">":
            #header line
            print(line)
        else:
            tok = line.split ( ':' )
            # start - end - score - pVal - eVal - strand - pattern :
            data['start'].append(tok[0])
            data['end'].append( tok[1] )
            data['score'].append( tok[2] )
            data['pVal'].append( tok[3] )
            data['eVal'].append( tok[4] )
            data['strand'].append ( tok[5] )
            data['pattern'].append ( tok[6].strip() )

trace1 = go.Histogram(x=data['start'] )
dat=go.Data([trace1])
layout=go.Layout(title="Motif Occurrence", xaxis={'title':'Position on Sequence'}, yaxis={'title':'Counts'})
figure=go.Figure(data=dat,layout=layout)
div = opy.plot(figure, auto_open=False, output_type='div')
