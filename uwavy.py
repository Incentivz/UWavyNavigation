import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from scipy import misc
from itertools import product, starmap
from PIL import Image
from skimage.transform import resize
import skimage
from matplotlib.animation import FuncAnimation
from IPython.core.display import HTML

# Globals
plt.rcParams['figure.figsize'] = 12, 8
ref_img = np.array(Image.open('manhattan.jpg'))
RADIUS = 180

def wide_uturn(leg=10):
    ones = np.ones((leg,1));
    zeros = np.zeros((leg,1));

    leg1 = np.hstack((ones, zeros))
    leg2 = np.hstack((zeros, ones))
    leg3 = np.hstack((-ones, zeros))
    return np.concatenate((leg1, leg2, leg3), axis=0)

def s_turn(short_leg=5):
    ones = np.ones((short_leg,1));
    zeros = np.zeros((short_leg,1));

    leg1 = np.hstack((ones, zeros))
    leg2 = np.hstack((zeros*2, -ones*2))
    leg3 = np.hstack((ones, zeros))
    return np.concatenate((leg1, leg2, leg3), axis=0)

def imread(path, grayscale=False):
    if grayscale:
        img = np.array(Image.open(path).convert('L'))
    else:
        img = np.array(Image.open(path))

    return np.swapaxes(img, 0, 1)

def take_picture(drone_position):
    x_center = drone_position[0]
    y_center = drone_position[1]
    return ref_img[x_center - RADIUS : x_center + RADIUS, y_center - RADIUS : y_center + RADIUS]

def plot_ref_img(ax=None, drone_pos=None, crop_height=1):
    if ax is None:
        plt.title("Reference Image")
        ax = plt
    else:
        ax.set_title("Reference Image")
    ax.imshow(ref_img.take(range(int(ref_img.shape[0] * crop_height)), axis=0), alpha = 1 if drone_pos is None else .75 );
    ax.axis('off');
    
    if drone_pos is not None:
        from matplotlib.patches import Rectangle;
        N = 150;
        pos = np.flip(drone_pos - RADIUS)
        ax.add_patch(Rectangle(pos, RADIUS * 2, RADIUS * 2, color="dodgerblue", fill=False, linewidth=3, label="Camera View"));
        plt.legend()
        
def plot_line_error(drone_position, ax):
    # Plot a horizontal line representing the positions searched
    ax.axhline(drone_position[0])
    
    # Take successive slices of REF_IMG along a vertical axis that runs through (x,y) and plot the error 
    ref_slice = take_picture(drone_position)
    errs = []
    rng = range(0, ref_img.shape[1], 5)
    for i, x in enumerate(rng):
        test_slice = take_picture((x + RADIUS, drone_position[0]))
        err = np.sum(np.square(test_slice - ref_slice)) / (4*RADIUS*RADIUS)
        errs.append(err)
    errs = np.array(errs)
    ax.twinx().plot(rng, errs, 'r', linewidth=3, label="Mean Squared Error");
    
def plot_heat_map(drone_position, ax):
    if ax is None:
        plt.title("Error Heatmap")
        ax = plt
    else:
        ax.set_title("Error Heatmap")
    # Take a sample of size NxN centered at drone_position
    ref_slice = take_picture(drone_position)

    # Make a heatmap showing the differences between slices taken at each point on the map and the test slice
    x_rng, y_rng = [range(RADIUS, ref_img.shape[i] - RADIUS, 25) for i in (0,1)]
    errs = np.zeros((len(x_rng), len(y_rng)))
    for (i,x) in enumerate(x_rng):
        for (j,y) in enumerate(y_rng):
            test_img = take_picture((x,y))
            err = np.sum(np.square(test_img - ref_slice)) / (4*RADIUS*RADIUS)
            errs[i][j] = err

    # Resize the heatmap to match the original image
    errs = skimage.transform.resize(errs, (ref_img.shape[0] - RADIUS * 2, ref_img.shape[1] - RADIUS * 2)).copy()
    errs_new = np.ones(ref_img.shape[0:2]) * errs.mean()
    errs_new[RADIUS:-RADIUS,RADIUS:-RADIUS] = errs
    errs = errs_new

    ax.imshow(errs, cmap="afmhot", interpolation='nearest')

class FlightAnimator:

    def __init__(self, framerate = 10):
        self.lines = []
        self.fig, self.axs = plt.subplots(2,1, figsize=(7,5), gridspec_kw={'height_ratios': [10, 1]})
        self.fig.tight_layout()
        self.axs[1].axis('off')
        self.ax = self.axs[0]
        
        self.img = ref_img

        self.paths = []
        self.start = None
        self.end = None
        self.ani_obj = None

        self.framerate = framerate


    def addPath(self, path, color, label):
        lobjline = self.ax.plot([],[],lw=2, color=color, alpha=0.5, label=label)[0]
        lobjmarker = self.ax.plot([],[],color=color, marker='d')[0]

        self.lines.append(lobjline)
        self.lines.append(lobjmarker)

        self.paths.append(path)

    def add_start(self, start):
        self.start = start

    def add_end(self, end):
        self.end = end


    def initAnimation(self):
        for line in self.lines:
            line.set_data([],[])
        self.ax.imshow(self.img, alpha=.5, interpolation='none')
        logo = np.rot90(imread('logo.png'))
        self.axs[1].imshow(logo, origin='lower', interpolation='none')
        if self.start is not None:
            self.ax.text(self.start[0], self.start[1], 'A', color='w', bbox=dict(facecolor='black', alpha=0.4))
        if self.end is not None:
            self.ax.text(self.end[0], self.end[1], 'B', color='w', bbox=dict(facecolor='black', alpha=0.4))
        self.ax.legend(loc='best')

        self.ax.axis('equal')
        self.ax.axis('off')
        FIELD_OF_VIEW = 500
        self.ax.set_xlim(self.paths[0].min(axis=0)[0] - FIELD_OF_VIEW//2, self.paths[0].max(axis=0)[0] + FIELD_OF_VIEW//2)
        self.ax.set_ylim(self.paths[0].min(axis=0)[1] - FIELD_OF_VIEW//2, self.paths[0].max(axis=0)[1] + FIELD_OF_VIEW//2)
        return self.lines

    def animate_path(self, i):
        for j, line in enumerate(self.lines):
            #only do every other, add marker and line at once
            if j % 2 == 0:
                path_j = j //2
                cur_path = self.paths[path_j]
                self.lines[j].set_data(cur_path[0:i,0], cur_path[0:i,1])
                marker_index = i - 1 if i > 0 else 0
                self.lines[j + 1].set_data(cur_path[marker_index,0], cur_path[marker_index,1])
        return self.lines

    def toHTML5Video(self):
        return FuncAnimation(self.fig, 
                             self.animate_path, 
                             init_func=self.initAnimation, 
                             frames=len(self.paths[0]) + 1, 
                             blit=True, 
                             interval = self.framerate
                            ).to_html5_video()
