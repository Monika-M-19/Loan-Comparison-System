from matplotlib.ticker import FuncFormatter


def format_indian_number(value):
    value = int(round(value))
    sign = "-" if value < 0 else ""
    digits = str(abs(value))

    if len(digits) <= 3:
        return f"{sign}{digits}"

    last_three = digits[-3:]
    remaining = digits[:-3]
    groups = []

    while len(remaining) > 2:
        groups.insert(0, remaining[-2:])
        remaining = remaining[:-2]

    if remaining:
        groups.insert(0, remaining)

    return f"{sign}{','.join(groups + [last_three])}"


def format_indian_currency(value):
    return f"₹{format_indian_number(value)}"


def update_graph(
    fig,
    canvas,
    public_rate,
    private_rate,
    emi1,
    emi2,
    interest1,
    interest2,
    tot1,
    tot2,
    principal
):
    fig.clf()
    fig.patch.set_facecolor("#ffffff")

    ax1 = fig.add_subplot(131)
    ax2 = fig.add_subplot(132)
    ax3 = fig.add_subplot(133)

    colors = ["#bbf7d0", "#bae6fd"]
    edge_colors = ["#16a34a", "#0284c7"]

    for ax in (ax1, ax2, ax3):
        ax.set_facecolor("#ffffff")
        ax.tick_params(colors="#64748b")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        for spine in ax.spines.values():
            spine.set_color("#d5dde8")

    def add_bar_labels(ax, bars, formatter, max_value):
        for bar in bars:
            value = bar.get_height()
            label = formatter(value)
            label_size = 9 if len(label) > 11 else 10
            offset = max_value * 0.035
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                value + offset,
                label,
                ha="center",
                va="bottom",
                color="#334155",
                fontsize=label_size,
                fontweight="bold"
            )

    bars1 = ax1.bar(
        ["Public", "Private"],
        [public_rate, private_rate],
        color=colors,
        edgecolor=edge_colors,
        linewidth=1.2,
        width=0.48
    )
    ax1.set_title("ROI", color="#172033", fontweight="bold")
    ax1.set_ylabel("Rate (%)", color="#64748b")
    ax1.grid(axis="y", alpha=0.35, color="#d5dde8")
    roi_max = max(public_rate, private_rate)
    ax1.set_ylim(0, roi_max * 1.35)
    add_bar_labels(ax1, bars1, lambda value: f"{value:.2f}%", roi_max)

    bars2 = ax2.bar(
        ["Public", "Private"],
        [emi1, emi2],
        color=colors,
        edgecolor=edge_colors,
        linewidth=1.2,
        width=0.48
    )
    ax2.set_title("Monthly EMI", color="#172033")
    ax2.set_ylabel("Amount (Rs.)", color="#64748b")
    ax2.yaxis.set_major_formatter(
        FuncFormatter(lambda value, position: format_indian_currency(value))
    )
    ax2.grid(axis="y", alpha=0.35, color="#d5dde8")
    emi_max = max(emi1, emi2)
    ax2.set_ylim(0, emi_max * 1.35)
    add_bar_labels(ax2, bars2, format_indian_currency, emi_max)

    bars3 = ax3.bar(
        ["Public", "Private"],
        [tot1, tot2],
        color=colors,
        edgecolor=edge_colors,
        linewidth=1.2,
        width=0.48
    )
    ax3.set_title("Total Repayment", color="#172033")
    ax3.set_ylabel("Amount (Rs.)", color="#64748b")
    ax3.yaxis.set_major_formatter(
        FuncFormatter(lambda value, position: format_indian_currency(value))
    )
    ax3.grid(axis="y", alpha=0.35, color="#d5dde8")
    total_max = max(tot1, tot2)
    ax3.set_ylim(0, total_max * 1.42)
    add_bar_labels(ax3, bars3, format_indian_currency, total_max)

    fig.tight_layout(pad=2.2, w_pad=2.2)
    canvas.draw_idle()
    canvas.flush_events()
