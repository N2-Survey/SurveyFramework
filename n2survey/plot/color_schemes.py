import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap


def example_plot(palette):
    plt.figure(figsize=(len(palette), 1))
    sns.set_theme(palette=palette)
    plt.axis("off")
    dx = 1 / len(palette)
    for i, p in enumerate(palette):
        sns.scatterplot(x=i * dx, y=np.ones(len(palette)), s=500, marker="s")
    plt.show()


class ColorSchemes:
    base_colors = {
        "MPS": [np.array([201, 219, 216]) / 255, np.array([4, 117, 105]) / 255],
        "Leibniz": [
            np.array([173, 173, 211]) / 255,
            np.array([226, 142, 98]) / 255,
            np.array([219, 223, 84]) / 255,
            np.array([111, 152, 204]) / 255,
        ],
        "Helmholtz": [
            np.array([0, 40, 100]) / 255,
            np.array([34, 176, 248]) / 255,
            np.array([143, 184, 39]) / 255,
        ],
        "TUM": [np.array([230, 230, 230]) / 255, np.array([48, 112, 179]) / 255],
        "N2": [
            np.array([46, 71, 128]) / 255,
            np.array([26, 130, 161]) / 255,
            np.array([229, 21, 109]) / 255,
        ],
    }

    @staticmethod
    def map_colors(n_colors, name):
        colors = ColorSchemes.base_colors[name]
        cmap = LinearSegmentedColormap.from_list(name, colors)
        c_list = [
            cmap(i, alpha=False) for i in np.linspace(0, 1, n_colors, endpoint=True)
        ]

        if name not in plt.colormaps():
            plt.register_cmap(name, cmap=cmap)

        return sns.color_palette(c_list)

    def __init__(self, n_colors=5):
        self.n_colors = n_colors
        self.mps = ColorSchemes.map_colors(n_colors, "MPS")
        self.leibniz = ColorSchemes.map_colors(n_colors, "Leibniz")
        self.helmholtz = ColorSchemes.map_colors(n_colors, "Helmholtz")
        self.tum = ColorSchemes.map_colors(n_colors, "TUM")
        self.n2_net = ColorSchemes.map_colors(n_colors, "N2")


# def main():
#     example_plot(ColorSchemes(5).mps)
#     example_plot(ColorSchemes(5).leibniz)
#     example_plot(ColorSchemes(5).helmholtz)
#     example_plot(ColorSchemes(5).tum)
#     example_plot(ColorSchemes().n2_net)
#
#
# if __name__ == "__main__":
#     main()
