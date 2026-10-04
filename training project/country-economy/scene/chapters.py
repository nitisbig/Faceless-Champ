"""Editorial scene compositions driven by word cues, never handwritten timestamps."""

from faceless_champ import Axis, BarChart, ChartStyle, Line, Rectangle

from .design import (
    IVORY,
    RUST,
    SANS,
    SCHEME,
    TAUPE,
    card,
    connector,
    flow_nodes,
    icon,
    image,
    number,
    text,
)


def opening(b):
    photo = image(1, 510, 545, 800, 510, b.image_mode)
    b.show(1, photo, note="morning news / image 1.png")
    alerts = []
    for cue, title, symbol, y in [
        (13, "Government funds", "government", 355),
        (19, "Nervous banks", "savings", 505),
        (22, "Investors sell bonds", "bond", 655),
        (29, "Currency falls", "down", 805),
    ]:
        items = card(title, 1395, y, symbol=symbol, width=690, height=120)
        b.show(cue, *items, motion=True, note=title)
        alerts.extend(items)
    b.retire(40, photo, *alerts)
    b.show(
        40,
        text("What does it actually mean?", 960, 515, 104, serif=True),
        text("An entire country. Out of money.", 960, 675, 42, color=RUST),
        motion=True,
    )


def household(b):
    b.show(
        54,
        icon("person", 465, 430, 130),
        text("A household", 465, 340, 44, serif=True),
        text("Bank balance", 465, 580, 30),
        text("A government", 1400, 340, 44, serif=True),
    )
    balance = number(1, 465, 705, 130, prefix="$", format_spec=".0f")
    b.show(63, balance, note="household bank balance")
    b.change(72, balance.animate.value_to(0), duration=0.001, note="balance reaches zero")
    building = image(2, 1390, 600, 750, 440, b.image_mode)
    b.show(54, building, note="government / image 2.png")
    b.retire(74, building)
    for cue, title, symbol, x, y in [
        (77, "Collect taxes", "tax", 1140, 480),
        (78, "Borrow", "bond", 1600, 480),
        (80, "Sell assets", "government", 1140, 710),
        (87, "Create\ncurrency*", "money", 1600, 710),
    ]:
        b.show(cue, *card(title, x, y, symbol=symbol, width=420, height=180), motion=True, note=title)
    b.show(90, text("*Where the monetary system permits", 1390, 850, 26))
    b.show(110, text("The constraint: paying what was promised", 960, 900, 38, color=RUST))


def budget(b):
    b.show(129, image(2, 960, 515, 390, 260, b.image_mode), text("GOVERNMENT", 960, 720, 27, color=RUST))
    b.show(138, text("MONEY IN", 340, 300, 28, color=RUST))
    for cue, label, symbol, y in [
        (142, "Income tax", "person", 405),
        (144, "Business tax", "factory", 535),
        (146, "Sales tax", "basket", 665),
        (148, "Import duties", "ship", 795),
    ]:
        b.show(cue, *card(label, 340, y, symbol=symbol, width=470, height=110), motion=True)
    b.draw(141, connector((595, 535), (735, 535)))
    b.show(150, text("MONEY OUT", 1510, 300, 28, color=RUST))
    b.draw(152, connector((1185, 535), (1280, 535)))
    for cue, label, symbol, x, y in [
        (156, "Roads", "road", 1400, 420),
        (157, "Hospitals", "hospital", 1700, 420),
        (158, "Schools", "school", 1400, 615),
        (159, "Workers", "people", 1700, 615),
        (161, "Pensions", "savings", 1400, 810),
        (163, "Military", "military", 1700, 810),
    ]:
        b.show(
            cue,
            Rectangle(width=270, height=170, corner_radius=12, fill=IVORY, stroke=None, position=(x, y)),
            icon(symbol, x, y - 28, 64),
            text(label, x, y + 49, 27),
            motion=True,
            note=label,
        )


def deficit(b):
    style = ChartStyle(scheme=SCHEME, colors=(TAUPE, RUST), font=SANS, font_size=30, legend=False, grid=False)
    chart = BarChart(
        ["Revenue", "Spending"],
        {"Revenue": [0, 0], "Spending": [0, 0]},
        stacked=True,
        width=1080,
        height=570,
        position=(705, 565),
        style=style,
        y_axis=Axis(limits=(0, 120), label="USD billions"),
    )
    b.show(168, chart, text("Illustrative annual budget", 690, 300, 26))
    revenue, spending = number(0, 490, 345, 84, suffix="B", prefix="$"), number(0, 975, 345, 84, suffix="B", prefix="$")
    b.show(172, revenue)
    b.change(
        172,
        chart.animate.data_to({"Revenue": [100, 0], "Spending": [0, 0]}),
        revenue.animate.value_to(100),
        duration=0.55,
        note="$100B collected",
    )
    b.show(176, spending)
    b.change(
        176,
        chart.animate.data_to({"Revenue": [100, 0], "Spending": [0, 110]}),
        spending.animate.value_to(110),
        duration=0.55,
        note="$110B spent",
    )
    b.show(
        181,
        Rectangle(width=470, height=300, corner_radius=16, fill=IVORY, stroke=None, position=(1530, 520)),
        text("The gap", 1530, 425, 46, serif=True),
        number(10, 1530, 555, 115, prefix="$", suffix="B"),
        note="$10B deficit",
    )
    b.show(183, text("DEFICIT", 1530, 700, 32, color=RUST), text("Spending − revenue", 1530, 780, 30))


def bonds(b):
    b.show(189, *card("The extra $10B", 960, 350, symbol="bond", width=730, height=135))
    b.show(
        203,
        icon("government", 1380, 545, 150),
        text("Government", 1380, 670, 44, serif=True),
        icon("people", 520, 545, 150),
        text("Investors", 520, 670, 44, serif=True),
    )
    b.show(
        210,
        Rectangle(width=300, height=230, fill=IVORY, stroke=TAUPE, corner_radius=10, position=(960, 560)),
        text("IOU", 960, 530, 88, serif=True, color=RUST),
        text("Government bond", 960, 610, 24),
        note="bond is an IOU",
    )
    b.draw(214, connector((620, 435), (1280, 435)))
    b.show(216, text("Money today", 960, 400, 29, color=RUST))
    b.draw(222, connector((1280, 790), (620, 790)))
    b.show(226, text("Repayment later + interest", 960, 850, 32, color=RUST))
    b.show(233, text("Borrowing is routine across major economies", 960, 915, 28))


def debt(b):
    b.show(237, icon("people", 1480, 430, 125), text("Will we get paid back?", 1480, 555, 46, serif=True))
    chart = BarChart(
        ["Year 1", "Year 2", "Year 3"],
        {"Debt": [0, 0, 0]},
        width=1050,
        height=550,
        position=(690, 590),
        style=ChartStyle(scheme=SCHEME, colors=(RUST,), font=SANS, font_size=28, legend=False, grid=False),
        y_axis=Axis(limits=(0, 320), label="USD billions"),
    )
    b.show(251, chart, text("Illustrative debt path", 650, 310, 27))
    for cue, values, x, amount in [
        (261, [100, 0, 0], 400, 100),
        (264, [100, 200, 0], 710, 200),
        (267, [100, 200, 300], 1020, 300),
    ]:
        b.change(cue, chart.animate.data_to({"Debt": values}), note=f"debt ${amount}B")
        b.show(cue, text(f"${amount}B", x, 390 - (amount - 100) * 0.2, 42, color=RUST))
    b.show(279, *card("Economic growth", 1490, 690, symbol="up", width=510, height=125))
    b.show(288, *card("Payments continue", 1490, 845, symbol="money", width=510, height=125))


def shocks(b):
    photo = image(3, 490, 535, 760, 450, b.image_mode)
    b.show(292, photo, note="economic shocks / image 3.png")
    labels = []
    for cue, label, symbol, y in [
        (301, "Recession", "down", 355),
        (304, "Tax revenue falls", "tax", 490),
        (309, "War", "warning", 625),
        (312, "Banking crisis", "savings", 760),
    ]:
        group = card(label, 1380, y, symbol=symbol, width=690, height=115)
        b.show(cue, *group, motion=True)
        labels.extend(group)
    warning = text("Natural disaster / aggressive borrowing", 960, 890, 32, color=RUST)
    b.show(315, warning)
    b.retire(327, photo, *labels, warning)
    b.show(327, text("THE PRICE OF BORROWING", 960, 355, 28, color=RUST))
    demand = text("Investors demand higher interest", 960, 560, 64, serif=True)
    b.show(330, demand)
    b.retire(341, demand)
    rate = number(3, 960, 560, 200, suffix="%")
    b.show(341, rate)
    for cue, value, x in [(341, 3, 390), (345, 6, 770), (347, 10, 1150), (350, 20, 1530)]:
        b.change(cue, rate.animate.value_to(value), duration=0.35, note=f"borrowing rate {value}%")
        b.show(cue, *card(f"{value}%", x, 790, width=300, height=150, accent=value == 20))


def interest_loop(b):
    flow_nodes(
        b,
        [
            (357, "Higher interest", "percent", 550, 420),
            (365, "More financing needed", "money", 1370, 420),
            (374, "More borrowing", "bond", 1370, 720),
            (383, "Investors worry", "warning", 550, 720),
        ],
        loop=True,
    )
    b.show(389, text("A self-reinforcing debt cycle", 960, 875, 38, color=RUST))
    b.show(
        399,
        Rectangle(
            width=850, height=100, fill=IVORY, stroke=RUST, stroke_width=2, corner_radius=12, position=(960, 570)
        ),
        text("Borrowing capacity runs out", 960, 570, 46, serif=True, color=RUST),
        note="lending becomes unavailable",
    )


def currency(b):
    b.show(
        415,
        *card("Own currency", 520, 380, symbol="money", width=780, height=150),
        *card("Foreign currency", 1400, 380, symbol="world", width=780, height=150),
    )
    b.show(435, icon("government", 520, 565, 130), text("US dollar system", 520, 695, 42, serif=True))
    b.show(451, text("Central bank can create dollars", 520, 775, 31, color=RUST))
    for cue, label, x in [(471, "Inflation", 320), (474, "Weaker currency", 620), (477, "Lost confidence", 920)]:
        b.show(cue, text(label, x, 880, 26, color=RUST))
    b.show(493, icon("government", 1400, 565, 130), text("Foreign-dollar debt", 1400, 695, 42, serif=True))
    b.show(507, text("Cannot create US dollars", 1400, 775, 32, color=RUST))
    b.show(517, text("Must obtain foreign currency", 1400, 850, 30))


def reserves(b):
    port = image(4, 480, 540, 750, 440, b.image_mode)
    b.show(519, port, note="exports / image 4.png")
    groups = []
    for cue, label, symbol, x, y in [
        (526, "Exports", "ship", 1130, 430),
        (528, "Investment", "factory", 1600, 430),
        (530, "International\nloans", "bond", 1130, 680),
        (534, "Reserves", "savings", 1600, 680),
    ]:
        items = card(label, x, y, symbol=symbol, width=430, height=185)
        b.show(cue, *items, motion=True)
        groups.extend(items)
    currencies = text("Dollars  /  Euros  /  Gold", 960, 875, 38, color=RUST)
    b.show(539, currencies)
    b.retire(547, port, *groups, currencies)
    tank = Rectangle(width=1000, height=160, fill=IVORY, stroke=TAUPE, corner_radius=8, position=(960, 560))
    reserve_bar = Rectangle(width=930, height=96, fill=RUST, stroke=None, position=(485, 512), anchor="top_left")
    reserve_heading = text("FOREIGN-CURRENCY RESERVES", 960, 350, 32)
    b.show(547, tank, reserve_bar, reserve_heading)
    # Shrink to the left edge; this is a conceptual stock, not numerical country data.
    b.change(552, reserve_bar.animate.scale_to(0.7), duration=1.0, note="reserves begin shrinking")
    support = text("Central bank sells reserves to support its currency", 960, 750, 40, serif=True)
    b.show(561, support)
    b.change(571, reserve_bar.animate.scale_to(0.25), duration=1.0, note="reserves sold")
    finite = text("Reserves are finite", 960, 850, 42, color=RUST)
    b.show(579, finite)
    b.retire(580, tank, reserve_bar, reserve_heading, support, finite)
    b.show(580, image(5, 495, 535, 750, 430, b.image_mode), note="imports / image 5.png")
    for cue, label, symbol, y in [
        (585, "Fuel", "energy", 365),
        (590, "Machinery", "factory", 495),
        (596, "Medicine", "hospital", 625),
        (597, "Food", "food", 755),
    ]:
        b.show(cue, *card(label, 1390, y, symbol=symbol, width=670, height=105), motion=True)
    b.show(607, text("A weaker currency makes imports harder", 960, 910, 32, color=RUST))


def conversion(b):
    debt = number(10, 960, 425, 145, prefix="$", suffix="B")
    fixed = text("FOREIGN DEBT STAYS FIXED", 960, 320, 30, color=RUST)
    b.show(610, fixed)
    b.show(620, debt, note="fixed $10B US debt")
    b.show(
        624,
        Rectangle(width=670, height=280, corner_radius=16, fill=IVORY, stroke=None, position=(520, 660)),
        Rectangle(width=670, height=280, corner_radius=16, fill=IVORY, stroke=None, position=(1400, 660)),
        text("Currency value", 520, 585, 42, serif=True),
        text("Local repayment cost", 1400, 585, 42, serif=True),
    )
    value, cost = number(100, 520, 720, 100, suffix="%"), number(1, 1400, 720, 100, suffix="×", format_spec=".1f")
    b.show(624, value, cost)
    b.change(628, value.animate.value_to(50), duration=0.8, note="currency loses half its value")
    b.draw(631, connector((890, 660), (1030, 660)))
    b.change(641, cost.animate.value_to(2), duration=0.65, note="local repayment cost doubles")
    b.show(646, text("Currency falls  ↔  Investors fear losses", 960, 895, 39, color=RUST))


def policies(b):
    positions = [(490, 410), (1430, 410), (490, 730), (1430, 730)]
    labels = [
        ("Austerity", "tax"),
        ("Emergency assistance", "deal"),
        ("Debt restructuring", "clock"),
        ("Default", "warning"),
    ]
    # The overview is introduced by 'several options'; details appear only when spoken.
    for (x, y), (label, symbol) in zip(positions, labels):
        b.show(672, *card(label, x, y, symbol=symbol, width=810, height=245))
    for cue, details, x, y in [
        (676, "Cut spending • subsidies • wages\nRaise taxes", 490, 470),
        (745, "Emergency loans\nEconomic reforms", 1430, 470),
        (762, "Pay later • lower rates\nNegotiate a smaller repayment", 490, 790),
        (808, "Debt payments missed", 1430, 790),
    ]:
        group = text(details, x, y, 27)
        b.show(cue, group, note=details.replace("\n", " / "))
    b.show(709, text("Austerity can weaken the economy", 960, 900, 32, color=RUST))
    b.show(742, text("IMF", 1660, 325, 27, color=RUST))


def aftermath(b):
    definition = text("Default = missed government debt payments", 960, 440, 58, serif=True, color=RUST)
    bond_icon = icon("bond", 960, 630, 150)
    b.show(809, definition, bond_icon)
    b.retire(822, definition, bond_icon)
    groups = []
    for cue, label, symbol, x in [
        (831, "Government", "government", 390),
        (834, "People work", "work", 960),
        (839, "Businesses operate", "factory", 1530),
    ]:
        items = card(label, x, 500, symbol=symbol, width=500, height=180)
        b.show(cue, *items)
        groups.extend(items)
    production = text("Food  •  Energy  •  Services  •  Goods", 960, 750, 44, serif=True)
    b.show(846, production)
    b.retire(854, *groups, production)
    trust = text("TRUST CHANGES", 960, 340, 34, color=RUST)
    b.show(854, trust)
    loss_groups = []
    for cue, label, symbol, x, y in [
        (860, "Less lending", "bond", 470, 500),
        (863, "Higher rates", "percent", 1450, 500),
        (868, "Bank losses", "savings", 470, 720),
        (872, "Currency falls", "down", 1450, 720),
    ]:
        items = card(label, x, y, symbol=symbol, width=790, height=165)
        b.show(cue, *items)
        loss_groups.extend(items)
    inflation = text("Inflation can accelerate", 960, 900, 33, color=RUST)
    b.show(875, inflation)
    b.retire(877, *loss_groups, trust, inflation)
    b.show(877, image(6, 495, 545, 730, 470, b.image_mode), note="household consequences / image 6.png")
    for cue, label, symbol, y in [
        (885, "Higher prices", "basket", 370),
        (886, "Unemployment", "work", 520),
        (887, "Shortages", "warning", 670),
        (890, "Less purchasing power", "wallet", 820),
    ]:
        b.show(cue, *card(label, 1390, y, symbol=symbol, width=700, height=120), motion=True)


def recap(b):
    groups = []
    for cue, label, symbol, x, y in [
        (916, "Borrowing capacity", "bond", 490, 460),
        (918, "Foreign currency", "exchange", 1430, 460),
        (920, "Investor confidence", "deal", 490, 720),
        (924, "Political room", "government", 1430, 720),
    ]:
        items = card(label, x, y, symbol=symbol, width=790, height=205)
        b.show(cue, *items, motion=True)
        groups.extend(items)
    b.retire(938, *groups)
    line = Line(length=1190, stroke=TAUPE, stroke_width=3, position=(960, 640))
    endurance = text("Debt can endure for decades", 960, 450, 76, serif=True)
    b.show(938, endurance)
    b.draw(946, line)
    belief = text("If people believe payments will continue", 960, 765, 38, color=RUST)
    warning = icon("warning", 1560, 600, 90)
    crisis = text("Lost belief can become a real crisis", 960, 880, 36)
    b.show(951, belief)
    b.show(959, warning)
    b.show(974, crisis)
    closing = [
        text("Confidence", 960, 520, 168, serif=True, color=RUST),
        text("keeps the financial system alive", 960, 710, 44, serif=True),
    ]
    b.retire(975, endurance, line, belief, warning, crisis)
    money = text("Money", 960, 520, 150, serif=True)
    b.show(979, money, motion=True, note="money in the financial system")
    b.retire(990, money)
    b.show(990, *closing, motion=True, duration=0.6, note="closing confidence statement")


AUTHORS = [
    opening,
    household,
    budget,
    deficit,
    bonds,
    debt,
    shocks,
    interest_loop,
    currency,
    reserves,
    conversion,
    policies,
    aftermath,
    recap,
]
