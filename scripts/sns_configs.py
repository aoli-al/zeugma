import seaborn as sns
import matplotlib.pyplot as plt

sns.set_style("whitegrid", {'axes.grid' : True})
sns.set_context("paper", font_scale=1.5)

plt.rcParams.update({'axes.edgecolor': 'black', 'axes.linewidth': 2, 'axes.grid': True, 'grid.linestyle': '--'})
plt.rcParams['figure.figsize'] = 8, 6

# colors = ['#FB8072', '#80B1D3', '#FDB462', '#B3DE69', '#FCCDE5', '#8DD3C7', '#FFFFB3', '#BEBADA']
colors = ['#2A587A', '#83B828', '#FABC75', '#F83A25', '#FDD8EB']
# colors = ['#648FFF', '#FFB000', '#DC267F','#FE6100', '#785EF0']
sns.palplot(colors)
sns.set_palette(sns.color_palette(colors), 5, 1)
# sns.set_palette("ch:start=.2,rot=-.3")
line_style = dict(linewidth = 2, markersize = 8, err_style = "bars", dashes = False)
sub_figure_title = {"fontweight": 700, 'fontname':'Times New Roman', 'fontsize': 18}
plt.tight_layout()