import matplotlib.pyplot as plt
import numpy as np


def get_rgb_list(pallete):
    return [c["rgb"] for c in pallete]


def example_plot(pallete):
    plt.figure(figsize=(len(pallete), 1))
    plt.axis('off')
    dx = 1/len(pallete)
    for i, p in enumerate(pallete):
        plt.scatter(i*dx, 1,  s=500, color=np.array(p["rgb"])/255, marker="s")
    plt.show()


class ColorSchemes:


    def __init__(self):
        pass
        #Todo check how lime survey plots generates the colors and adapt the
        # contet accordingly

        self.phd_net = [{"name": "Opal", "hex": "C9DBD8", "rgb": [201, 219, 216],
                         "cmyk": [8, 0, 1, 14], "hsb": [170, 8, 86],
                         "hsl": [170, 20, 82], "lab": [86, -7, -1]},
                        {"name": "Spanish Gray", "hex": "999999",
                         "rgb": [153, 153, 153], "cmyk": [0, 0, 0, 40],
                         "hsb": [0, 0, 60], "hsl": [0, 0, 60], "lab": [63, 0, 0]},
                        {"name": "Black", "hex": "000000", "rgb": [0, 0, 0],
                         "cmyk": [0, 0, 0, 100], "hsb": [0, 0, 0], "hsl": [0, 0, 0],
                         "lab": [0, 0, 0]},
                        {"name": "Pine Green", "hex": "047569", "rgb": [4, 117, 105],
                         "cmyk": [97, 0, 10, 54], "hsb": [174, 97, 46],
                         "hsl": [174, 93, 24], "lab": [44, -31, -1]},
                        {"name": "Opal", "hex": "A9CDC9", "rgb": [169, 205, 201],
                         "cmyk": [18, 0, 2, 20], "hsb": [173, 18, 80],
                         "hsl": [173, 26, 73], "lab": [80, -13, -2]}]


def main():
    cs = ColorSchemes()
    color_list  = get_rgb_list(cs.phd_net)
    example_plot(cs.phd_net)


if __name__ == "__main__":
    main()

