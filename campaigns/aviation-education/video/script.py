"""
How the NTSB Investigates a Plane Crash
Manim CE animation script.
Renders 3Blue1Brown-style educational explainer.
"""
from manim import *
import numpy as np

# Shared palette
BG = "#1C1C1C"
PRIMARY = "#58C4DD"      # blue — NTSB, crash sites, core
SECONDARY = "#83C167"    # green — safety, adoption, positive
ACCENT = "#FFFF00"       # yellow — emphasis, key numbers
WARNING = "#FF6B6B"      # red — barred, crash
NEUTRAL = "#888888"      # gray — axes, grids, support
WHITE = "#FFFFFF"

MONO = "Noto Sans Mono"


class Scene1_Hook(Scene):
    def construct(self):
        self.camera.background_color = BG

        title = Text("How the NTSB Investigates", font_size=36, color=PRIMARY, font=MONO)
        subtitle = Text("a Plane Crash", font_size=36, color=PRIMARY, font=MONO)
        subtitle.next_to(title, DOWN, buff=0.3)

        self.add_subcaption("Every time a plane crashes in the United States, a team shows up before the smoke clears.", duration=2.5)
        self.play(FadeIn(title, shift=UP), FadeIn(subtitle, shift=UP), run_time=1.5)
        self.wait(1.0)

        crash_site = Circle(radius=0.5, color=WARNING, fill_opacity=0.3)
        crash_label = Text("CRASH SITE", font_size=12, color=WARNING, font=MONO)
        crash_label.next_to(crash_site, DOWN, buff=0.2)
        crash_group = Group(crash_site, crash_label)
        crash_group.shift(DOWN * 2)

        self.add_subcaption("They do not work for the airline.", duration=1.2)
        self.play(GrowFromCenter(crash_group), run_time=1.0)
        self.wait(0.5)

        go_label = Text("GO TEAM", font_size=20, color=PRIMARY, font=MONO, weight=BOLD)
        go_label.next_to(crash_site, RIGHT, buff=0.5)

        lines = VGroup()
        for angle in [30, 90, 150, 210, 270, 330]:
            deg = angle * DEGREES
            line = Line(
                crash_site.get_center(),
                crash_site.get_center() + 1.2 * np.array([np.cos(deg), np.sin(deg), 0]),
                color=PRIMARY, stroke_width=2,
            )
            lines.add(line)

        self.add_subcaption("And what they find changes every flight you will ever take.", duration=2.5)
        self.play(
            Write(go_label, run_time=1.0),
            LaggedStart(*[GrowFromCenter(l, run_time=0.8) for l in lines], lag_ratio=0.2),
        )
        self.wait(2.0)

        self.play(FadeOut(Group(title, subtitle, crash_group, go_label, lines)), run_time=0.5)
        self.wait(0.3)


class Scene2_Stakes(Scene):
    def construct(self):
        self.camera.background_color = BG

        header = Text("Since 1967", font_size=28, color=NEUTRAL, font=MONO)
        header.to_edge(UP, buff=0.5)

        self.add_subcaption("The NTSB has investigated more than 154,000 aviation accidents.", duration=2.5)
        counter1 = Text("0", color=ACCENT, font=MONO, font_size=36)
        counter1.shift(UP * 1 + LEFT * 3)
        self.play(Write(header, run_time=1.0))
        # Animate counter through intermediate values
        intermediate1 = [50000, 100000, 154000]
        current = counter1
        for val in intermediate1:
            next_val = Text(f"{val:,}", color=ACCENT, font=MONO, font_size=36)
            next_val.move_to(counter1.get_center())
            self.play(Transform(current, next_val, run_time=0.8),)
            current = next_val
        self.wait(0.8)

        self.add_subcaption("They have issued more than 15,700 safety recommendations.", duration=2.5)
        counter2 = Text("0", color=ACCENT, font=MONO, font_size=36)
        counter2.next_to(counter1, DOWN, buff=0.8)
        intermediate2 = [8000, 12000, 15700]
        current2 = counter2
        for val in intermediate2:
            next_val = Text(f"{val:,}", color=ACCENT, font=MONO, font_size=36)
            next_val.move_to(counter2.get_center())
            self.play(Transform(current2, next_val, run_time=0.8))
            current2 = next_val
        self.wait(0.8)

        self.add_subcaption("Eighty-two percent of the closed recommendations were actually implemented.", duration=2.5)
        pct_label = Text("82% implemented", font_size=24, color=SECONDARY, font=MONO)
        pct_label.next_to(counter2, DOWN, buff=0.8)
        self.play(FadeIn(pct_label, shift=UP), run_time=1.0)
        self.wait(1.5)

        self.add_subcaption("In 2025 alone, they adopted 1,436 investigative reports.", duration=2.0)
        self.add_subcaption("That is eighteen percent more than 2024.", duration=2.0)
        self.add_subcaption("They issued 131 new safety recommendations.", duration=2.0)
        self.add_subcaption("Fourteen of them were marked urgent.", duration=2.0)

        box = Rectangle(width=5, height=2, color=NEUTRAL, stroke_width=1, fill_opacity=0.1)
        box.to_edge(DOWN, buff=0.8)

        stat_lines = VGroup(
            Text("2025: 1,436 reports", font_size=20, color=PRIMARY, font=MONO),
            Text("+18% over 2024", font_size=20, color=ACCENT, font=MONO),
            Text("131 new recommendations", font_size=20, color=PRIMARY, font=MONO),
            Text("14 marked urgent", font_size=20, color=WARNING, font=MONO),
        )
        stat_lines.arrange(DOWN, buff=0.3, aligned_edge=LEFT)
        stat_lines.move_to(box.get_center())

        self.play(Create(box), run_time=0.8)
        self.play(LaggedStart(*[FadeIn(l, shift=RIGHT, run_time=0.5) for l in stat_lines], lag_ratio=0.3))
        self.wait(1.5)

        self.add_subcaption("As one observer put it: I wish more industries treated their mistakes the same way the aviation industry and our NTSB does.", duration=3.0)
        quote_box = Rectangle(width=6, height=1.8, color=NEUTRAL, stroke_width=1, fill_opacity=0.15)
        quote_box.to_edge(DOWN, buff=0.8)
        quote = Text(
            '"I wish more industries treated\ntheir mistakes the same way\nthe aviation industry and our NTSB does."',
            font_size=18, color=WHITE, font=MONO,
        )
        quote.move_to(quote_box.get_center())
        source = Text("@wangtangkiki  ntsb.gov/about/reports", font_size=12, color=NEUTRAL, font=MONO)
        source.next_to(quote_box, DOWN, buff=0.2)

        self.play(
            box.animate.set_opacity(0),
            stat_lines.animate.set_opacity(0),
            run_time=0.3,
        )
        self.play(
            Create(quote_box, run_time=0.8),
            Write(quote, run_time=1.5),
            Write(source, run_time=0.5),
        )
        self.wait(2.0)

        self.play(FadeOut(Group(header, counter1, counter2, pct_label, box, quote_box, quote, source, stat_lines)), run_time=0.5)
        self.wait(0.3)


class Scene3_GoTeam(Scene):
    def construct(self):
        self.camera.background_color = BG

        header = Text("The Go Team", font_size=36, color=PRIMARY, font=MONO, weight=BOLD)
        header.to_edge(UP, buff=0.5)

        self.play(Write(header, run_time=1.0))
        self.wait(0.5)

        center_circle = Circle(radius=0.5, color=PRIMARY, fill_opacity=0.4)
        center_label = Text("Go Team\nIIC", font_size=14, color=PRIMARY, font=MONO)
        center_label.move_to(center_circle.get_center())
        center_group = Group(center_circle, center_label)
        center_group.shift(UP * 1)

        self.add_subcaption("The Go Team is on call twenty-four hours a day.", duration=2.0)
        self.add_subcaption("They are dispatched to the accident scene.", duration=1.5)
        self.add_subcaption("They are led by an Investigator-in-Charge — the IIC.", duration=2.0)
        self.play(GrowFromCenter(center_group), run_time=1.0)
        self.wait(0.5)

        roles = [
            ("Operations", UP, 2.5),
            ("Structures", UP + LEFT, 2.5),
            ("Systems", UP + RIGHT, 2.5),
            ("ATC", LEFT, 2.5),
            ("Weather", RIGHT, 2.5),
            ("Human\nPerformance", DOWN + LEFT, 2.5),
            ("Survival\nFactors", DOWN + RIGHT, 2.5),
            ("Powerplants", DOWN, 2.5),
            ("Metallurgy", DOWN + LEFT, 2.5, True),
            ("CVR/FDR", DOWN + RIGHT, 2.5, True),
        ]

        role_dots = VGroup()
        role_labels = VGroup()
        spokes = VGroup()

        for entry in roles:
            label_text = entry[0]
            direction = entry[1]
            dist = entry[2]
            extra_left = entry[3] if len(entry) > 3 else False

            direction_norm = direction / np.linalg.norm(direction)
            pos = center_group.get_center() + direction_norm * dist
            if extra_left:
                pos = pos + LEFT * 0.5

            dot = Dot(pos, radius=0.15, color=PRIMARY)
            label = Text(label_text, font_size=11, color=NEUTRAL, font=MONO)
            label.next_to(dot, direction, buff=0.3)

            role_dots.add(dot)
            role_labels.add(label)
            spoke = Line(
                center_group.get_center(),
                pos,
                color=NEUTRAL, stroke_width=1, stroke_opacity=0.5,
            )
            spokes.add(spoke)

        self.add_subcaption("Specialists cover every angle: operations, structures, systems, air traffic control, weather, human performance, survival factors, powerplants, metallurgy, and the cockpit and flight data recorders.", duration=5.0)
        self.play(
            LaggedStart(*[GrowFromCenter(d, run_time=0.3) for d in role_dots], lag_ratio=0.3),
            LaggedStart(*[FadeIn(l, run_time=0.3) for l in role_labels], lag_ratio=0.3),
            LaggedStart(*[GrowFromCenter(s, run_time=0.3) for s in spokes], lag_ratio=0.3),
        )
        self.wait(1.5)

        self.add_subcaption("This is a mobile lab.", duration=1.5)
        self.add_subcaption("The Go Team secures the site and starts the factual record.", duration=2.0)
        grid = NumberPlane(
            x_range=[-4, 4, 1], y_range=[-2, 2, 1],
            background_line_style={"stroke_color": NEUTRAL, "stroke_width": 1, "stroke_opacity": 0.2},
            faded_line_style={"stroke_opacity": 0.1},
        )
        grid.set_z_index(-1)
        doc_label = Text("Site secured. Documented.", font_size=16, color=SECONDARY, font=MONO)
        doc_label.to_edge(DOWN, buff=0.5)
        self.play(FadeIn(grid, run_time=1.0), Write(doc_label, run_time=0.8))
        self.wait(2.0)

        self.play(FadeOut(Group(header, center_group, role_dots, role_labels, spokes, grid, doc_label)), run_time=0.5)
        self.wait(0.3)


class Scene4_PartySystem(Scene):
    def construct(self):
        self.camera.background_color = BG

        header = Text("The Party System", font_size=36, color=PRIMARY, font=MONO, weight=BOLD)
        header.to_edge(UP, buff=0.5)
        self.play(Write(header, run_time=1.0))
        self.wait(0.5)

        # NTSB at center
        ntsb_node = Circle(radius=0.5, color=PRIMARY, fill_opacity=0.4)
        ntsb_label = Text("NTSB", font_size=16, color=PRIMARY, font=MONO, weight=BOLD)
        ntsb_label.move_to(ntsb_node.get_center())
        ntsb_group = Group(ntsb_node, ntsb_label)
        ntsb_group.shift(UP * 1)

        self.add_subcaption("The NTSB does not investigate alone.", duration=1.5)
        self.play(GrowFromCenter(ntsb_group), run_time=1.0)
        self.wait(0.5)

        parties = [
            ("Manufacturer", UP + LEFT * 1.8),
            ("FAA", UP + RIGHT * 1.8),
            ("Airline", LEFT * 2.8),
            ("Union", RIGHT * 2.8),
            ("Operator", DOWN * 1.8),
        ]

        party_groups = VGroup()
        arrows = VGroup()

        for label_text, pos_offset in parties:
            pos = ntsb_group.get_center() + pos_offset
            node = Circle(radius=0.35, color=SECONDARY, fill_opacity=0.3)
            label = Text(label_text, font_size=11, color=SECONDARY, font=MONO)
            label.next_to(node, UP, buff=0.25)
            group = VGroup(node, label)
            group.move_to(pos)
            party_groups.add(group)

            arrow = Arrow(
                ntsb_group.get_center(),
                pos,
                color=NEUTRAL, stroke_width=1.5,
                max_tip_length_to_length_ratio=0.2,
            )
            arrows.add(arrow)

        self.add_subcaption("Manufacturers, airlines, the FAA, unions, and sometimes the operator become parties.", duration=2.5)
        self.add_subcaption("They provide technical expertise during fact-finding.", duration=2.0)
        self.play(
            LaggedStart(*[GrowFromCenter(g, run_time=0.5) for g in party_groups], lag_ratio=0.3),
            LaggedStart(*[GrowFromPoint(a, a.get_start(), run_time=0.5) for a in arrows], lag_ratio=0.3),
        )
        self.wait(1.5)

        self.add_subcaption("Legal or litigation representatives are barred from the party system.", duration=2.5)
        litigation_icon = Square(side_length=0.6, color=WARNING)
        lit_label = Text("LITIGATOR", font_size=9, color=WARNING, font=MONO)
        lit_label.next_to(litigation_icon, DOWN, buff=0.12)
        litigation_group = VGroup(litigation_icon, lit_label)
        litigation_group.to_edge(DOWN, buff=1.0).shift(LEFT * 3)

        x_mark = VGroup(
            Line(litigation_icon.get_corner(UL), litigation_icon.get_corner(DR), color=WARNING, stroke_width=4),
            Line(litigation_icon.get_corner(UR), litigation_icon.get_corner(DL), color=WARNING, stroke_width=4),
        )

        self.play(FadeIn(litigation_group, run_time=0.5))
        self.wait(0.5)
        self.play(*[Create(x, run_time=0.8) for x in x_mark])
        self.wait(1.0)

        self.add_subcaption("The FAA is automatically a party by law. Every investigation. No exceptions.", duration=2.5)
        fact_card = Rectangle(width=2.5, height=1, color=NEUTRAL, stroke_width=1, fill_opacity=0.15)
        fact_card.to_edge(DOWN, buff=1.0).shift(RIGHT * 3)
        fact_text = Text("FAA = automatic\nparty, by law", font_size=14, color=SECONDARY, font=MONO)
        fact_text.move_to(fact_card.get_center())

        self.play(
            Create(fact_card, run_time=0.5),
            Write(fact_text, run_time=0.8),
        )
        self.wait(1.5)

        insight = Text(
            "Experts in the room during fact-finding.\nProfits kept out during analysis.",
            font_size=16, color=ACCENT, font=MONO,
        )
        insight.to_edge(DOWN, buff=0.3)

        self.add_subcaption("The experts are in the room during fact-finding.", duration=1.5)
        self.add_subcaption("The people who would profit from a soft report are not in the room during analysis.", duration=3.0)
        self.play(FadeIn(insight, shift=UP), run_time=1.0)
        self.wait(2.0)

        self.play(FadeOut(Group(header, ntsb_group, party_groups, arrows, litigation_group, x_mark, fact_card, fact_text, insight)), run_time=0.5)
        self.wait(0.3)


class Scene5_Timeline(Scene):
    def construct(self):
        self.camera.background_color = BG

        header = Text("Investigation Timeline", font_size=32, color=PRIMARY, font=MONO, weight=BOLD)
        header.to_edge(UP, buff=0.5)
        self.play(Write(header, run_time=1.0))
        self.wait(0.5)

        timeline = Line(LEFT * 5, RIGHT * 5, color=NEUTRAL, stroke_width=2)
        timeline.shift(DOWN * 0.5)

        classes = [
            ("Class 1\n(major)", LEFT * 4, ACCENT),
            ("Class 2", LEFT * 1.5, PRIMARY),
            ("Class 3", RIGHT * 1.5, SECONDARY),
            ("Class 4\n(6-mo)", RIGHT * 4, ACCENT),
        ]

        class_dots = VGroup()
        class_labels = VGroup()

        for label_text, x_pos, color in classes:
            x_coord = timeline.get_left()[0] + x_pos[0] + 5
            dot = Dot(np.array([x_coord, 0, 0]), radius=0.12, color=color)
            label = Text(label_text, font_size=14, color=color, font=MONO)
            label.next_to(dot, UP, buff=0.3)
            class_dots.add(dot)
            class_labels.add(label)

        range_label = Text("12–24 months\ntypical", font_size=16, color=ACCENT, font=MONO)
        range_label.to_edge(UP, buff=1.0).shift(DOWN * 0.5)

        self.add_subcaption("An NTSB investigation takes twelve to twenty-four months.", duration=2.5)
        self.add_subcaption("Class 1 — major, transport-category accidents — down to Class 4 with a six-month final report.", duration=4.0)
        self.play(
            Create(timeline, run_time=1.0),
            Write(range_label, run_time=0.8),
        )
        self.wait(0.5)
        self.play(
            LaggedStart(*[GrowFromCenter(d, run_time=0.3) for d in class_dots], lag_ratio=0.3),
            LaggedStart(*[FadeIn(l, run_time=0.3) for l in class_labels], lag_ratio=0.3),
        )
        self.wait(1.0)

        self.add_subcaption("Alaska Airlines Flight 1282 — January 2024 to June 2025. Seventeen months.", duration=3.0)
        self.add_subcaption("DCA mid-air collision — January 2025 to March 2025. Two months to urgent recommendations.", duration=3.0)

        alaska_box = Rectangle(width=5, height=0.8, color=NEUTRAL, stroke_width=1, fill_opacity=0.1)
        alaska_box.to_edge(DOWN, buff=1.0).shift(UP * 0.5)
        alaska_text = Text("Alaska 1282: Jan 2024 -> Jun 2025  (17 months)", font_size=14, color=PRIMARY, font=MONO)
        alaska_text.move_to(alaska_box.get_center())

        self.play(
            Create(alaska_box, run_time=0.5),
            Write(alaska_text, run_time=1.0),
        )
        self.wait(1.5)

        dca_box = Rectangle(width=4, height=0.8, color=NEUTRAL, stroke_width=1, fill_opacity=0.1)
        dca_box.next_to(alaska_box, DOWN, buff=0.4)
        dca_text = Text("DCA collision: Jan 2025 -> Mar 2025  (2 months)", font_size=14, color=WARNING, font=MONO)
        dca_text.move_to(dca_box.get_center())

        self.play(
            Create(dca_box, run_time=0.5),
            Write(dca_text, run_time=1.0),
        )
        self.wait(2.0)

        self.play(FadeOut(Group(header, timeline, range_label, class_dots, class_labels, alaska_box, alaska_text, dca_box, dca_text)), run_time=0.5)
        self.wait(0.3)


class Scene6_PublicRecord(Scene):
    def construct(self):
        self.camera.background_color = BG

        header = Text("The Public Record", font_size=32, color=PRIMARY, font=MONO, weight=BOLD)
        header.to_edge(UP, buff=0.5)
        self.play(Write(header, run_time=1.0))
        self.wait(0.5)

        interface = Rectangle(width=6, height=3.5, color=NEUTRAL, stroke_width=1, fill_opacity=0.15)
        interface.shift(UP * 0.5)

        fields = [("Date", NEUTRAL), ("Location", NEUTRAL), ("FAR Part", NEUTRAL), ("Injury Level", NEUTRAL)]

        field_boxes = VGroup()
        field_labels = VGroup()
        start_y = interface.get_top()[1] - 0.4
        for i, (field_name, color) in enumerate(fields):
            y_pos = start_y - i * 0.5
            box = Rectangle(width=1.5, height=0.4, color=color, stroke_width=1, fill_opacity=0.05)
            box.move_to(np.array([-1.5, y_pos, 0]))
            label = Text(field_name, font_size=14, color=color, font=MONO)
            label.move_to(np.array([-1.5, y_pos, 0]))
            field_boxes.add(box)
            field_labels.add(label)

        search_btn = RoundedRectangle(corner_radius=0.1, width=1, height=0.4, color=PRIMARY, stroke_width=1, fill_opacity=0.3)
        search_btn.move_to(np.array([1.8, start_y, 0]))
        search_text = Text("SEARCH", font_size=12, color=PRIMARY, font=MONO, weight=BOLD)
        search_text.move_to(search_btn.get_center())

        self.add_subcaption("The NTSB Aviation Investigation Search database contains civil accidents and selected incidents.", duration=3.0)
        self.add_subcaption("Query by date, location, FAR part, and injury level.", duration=2.5)
        self.play(
            Create(interface, run_time=1.0),
            LaggedStart(*[FadeIn(b, shift=UP, run_time=0.3) for b in field_boxes], lag_ratio=0.2),
            LaggedStart(*[FadeIn(l, shift=UP, run_time=0.3) for l in field_labels], lag_ratio=0.2),
            Create(search_btn, run_time=0.5),
            Write(search_text, run_time=0.5),
        )
        self.wait(1.0)

        self.add_subcaption("This is not a PR database.", duration=1.5)
        self.add_subcaption("It is the raw factual record.", duration=1.5)
        self.add_subcaption("Anyone can search it.", duration=1.5)
        fact = Text(
            "Raw factual record.\nAnyone can search it.\nntsb.gov/Pages/AviationQueryv2.aspx",
            font_size=16, color=SECONDARY, font=MONO,
        )
        fact.to_edge(DOWN, buff=0.5)
        self.play(Write(fact, run_time=1.5))
        self.wait(2.0)

        self.play(FadeOut(Group(header, interface, field_boxes, field_labels, search_btn, search_text, fact)), run_time=0.5)
        self.wait(0.3)


class Scene7_InvisibleSystem(Scene):
    def construct(self):
        self.camera.background_color = BG

        header = Text("The Invisible Safety System", font_size=28, color=PRIMARY, font=MONO, weight=BOLD)
        header.to_edge(UP, buff=0.5)
        self.play(Write(header, run_time=1.0))
        self.wait(0.5)

        self.add_subcaption("Aviation media covers every crash.", duration=1.5)
        self.add_subcaption("It has almost nothing to say about the flights that go right.", duration=2.5)
        self.add_subcaption("You hear about the one that failed.", duration=1.5)
        self.add_subcaption("You do not hear about the 99.999 percent that did not.", duration=2.0)

        green_dots = VGroup()
        np.random.seed(42)
        for _ in range(120):
            x = np.random.uniform(-5, 5)
            y = np.random.uniform(-2, 1)
            dot = Dot(np.array([x, y, 0]), radius=0.08, color=SECONDARY)
            green_dots.add(dot)

        red_dot = Dot(np.array([0, -0.5, 0]), radius=0.2, color=WARNING)

        labels = VGroup(
            Text("What you see", font_size=18, color=WARNING, font=MONO).next_to(red_dot, DOWN, buff=0.5),
            Text("What you don't", font_size=18, color=SECONDARY, font=MONO).next_to(green_dots[0], UP, buff=0.3),
        )

        self.play(
            LaggedStart(*[FadeIn(d, run_time=0.2) for d in green_dots], lag_ratio=0),
            run_time=3.0,
        )
        self.wait(0.5)
        self.play(GrowFromCenter(red_dot, run_time=0.5), Write(labels[0], run_time=0.5))
        self.wait(2.0)

        quote = Text(
            '"Aviation media covers every crash.\nIt has almost nothing to say\nabout the flights that go right."',
            font_size=16, color=NEUTRAL, font=MONO,
        )
        quote.next_to(labels[0], DOWN, buff=0.5)
        quote_source = Text("@Ecaspu  faasafety.gov", font_size=12, color=NEUTRAL, font=MONO)
        quote_source.next_to(quote, DOWN, buff=0.2)

        self.play(Write(quote, run_time=1.0), Write(quote_source, run_time=0.5))
        self.wait(1.5)

        self.play(
            FadeOut(Group(quote, quote_source, labels)),
            FadeOut(green_dots, run_time=1.0),
            FadeOut(red_dot, run_time=0.5),
        )
        self.wait(0.5)

        self.add_subcaption("Every investigation produces findings.", duration=1.5)
        self.add_subcaption("The findings become recommendations.", duration=1.5)
        self.add_subcaption("The recommendations get adopted.", duration=1.5)
        self.add_subcaption("The next generation of aircraft and procedures is safer.", duration=2.0)

        steps = [
            ("Investigation", PRIMARY),
            ("Findings", PRIMARY),
            ("Recommendations", ACCENT),
            ("Adoption", SECONDARY),
            ("Safer Next\nGeneration", SECONDARY),
        ]

        step_groups = VGroup()
        arrows_flow = VGroup()
        start_x = -4

        for i, (label_text, color) in enumerate(steps):
            box = Rectangle(width=2, height=1, color=color, stroke_width=1, fill_opacity=0.15)
            box.move_to(np.array([start_x + i * 2.5, 1, 0]))
            label = Text(label_text, font_size=11, color=color, font=MONO)
            label.move_to(box.get_center())
            step_groups.add(VGroup(box, label))

            if i < len(steps) - 1:
                next_x = start_x + (i + 1) * 2.5
                arrow = Arrow(
                    box.get_right(),
                    np.array([next_x, 1, 0]),
                    color=NEUTRAL, stroke_width=2,
                    max_tip_length_to_length_ratio=0.2,
                )
                arrows_flow.add(arrow)

        self.play(
            LaggedStart(*[FadeIn(b, shift=UP, run_time=0.5) for b in step_groups], lag_ratio=0.4),
        )
        self.wait(0.5)
        self.play(
            LaggedStart(*[GrowFromPoint(a, a.get_start(), run_time=0.5) for a in arrows_flow], lag_ratio=0.4),
        )
        rec_group = step_groups[2]
        self.play(
            rec_group[0].animate.set_fill_opacity(0.5),
            run_time=0.3,
        )
        self.wait(0.3)
        self.play(
            rec_group[0].animate.set_fill_opacity(0.15),
            run_time=0.3,
        )
        self.wait(1.5)

        chart_label = Text("GA Fatal Accident Rate", font_size=20, color=PRIMARY, font=MONO)
        chart_label.to_edge(DOWN, buff=1.5)

        # Manual chart: positioned at bottom of screen
        chart_origin = np.array([-2.5, -1.0, 0])  # bottom-left of chart area
        chart_w = 5.0   # x range width
        chart_h = 1.8   # y range height
        x_min_year = 2009
        x_max_year = 2025
        y_min_val = 0.6
        y_max_val = 0.9

        x_scale = chart_w / (x_max_year - x_min_year)
        y_scale = chart_h / (y_max_val - y_min_val)

        def year_to_x(year):
            return chart_origin[0] + (year - x_min_year) * x_scale

        def val_to_y(val):
            return chart_origin[1] + (val - y_min_val) * y_scale

        # Axes lines
        x_axis = Line(
            np.array([chart_origin[0], chart_origin[1], 0]),
            np.array([chart_origin[0] + chart_w, chart_origin[1], 0]),
            color=NEUTRAL, stroke_width=1,
        )
        y_axis = Line(
            np.array([chart_origin[0], chart_origin[1], 0]),
            np.array([chart_origin[0], chart_origin[1] + chart_h, 0]),
            color=NEUTRAL, stroke_width=1,
        )

        # Axis labels
        axis_labels = VGroup()
        for year in [2009, 2017, 2024]:
            lbl = Text(str(year), font_size=11, color=NEUTRAL, font=MONO)
            lbl.move_to(np.array([year_to_x(year), chart_origin[1] - 0.3, 0]))
            axis_labels.add(lbl)
        for val in [0.6, 0.7, 0.8, 0.9]:
            lbl = Text(str(val), font_size=11, color=NEUTRAL, font=MONO)
            lbl.move_to(np.array([chart_origin[0] - 0.3, val_to_y(val), 0]))
            axis_labels.add(lbl)

        axes = VGroup(x_axis, y_axis, axis_labels)

        # Data points: FY17 = 0.83, FY24 = 0.68
        dots_data = [(2017, 0.83), (2024, 0.68)]
        dot_mobjects = VGroup()
        label_mobjects = VGroup()

        for x, y in dots_data:
            pt = Dot(np.array([year_to_x(x), val_to_y(y), 0]), radius=0.1, color=PRIMARY)
            dot_mobjects.add(pt)
            lbl = Text(f"{y}", font_size=12, color=PRIMARY, font=MONO)
            lbl.next_to(pt, UP, buff=0.2)
            label_mobjects.add(lbl)

        # Line connecting the two points
        line = Line(
            dot_mobjects[0].get_center(),
            dot_mobjects[1].get_center(),
            color=SECONDARY, stroke_width=2,
        )

        self.add_subcaption("Fiscal year 2024 saw the lowest rate on record: 0.68 fatal accidents per 100,000 flight hours.", duration=3.5)
        self.add_subcaption("Down from 0.83 in fiscal year 2017.", duration=2.0)
        self.play(
            Write(chart_label, run_time=0.5),
            Create(axes, run_time=1.0),
        )
        self.play(
            Create(line, run_time=1.0),
            LaggedStart(*[GrowFromCenter(d, run_time=0.5) for d in dot_mobjects], lag_ratio=0.5),
            LaggedStart(*[FadeIn(l, run_time=0.5) for l in label_mobjects], lag_ratio=0.5),
        )
        self.wait(2.5)

        self.play(FadeOut(Group(header, step_groups, arrows_flow, rec_group, chart_label, axes, line, dot_mobjects, label_mobjects)), run_time=0.5)
        self.wait(0.3)


class Scene8_PayoffCTA(Scene):
    def construct(self):
        self.camera.background_color = BG

        crash_site = Circle(radius=0.4, color=WARNING, fill_opacity=0.3)
        crash_label = Text("CRASH", font_size=14, color=WARNING, font=MONO)
        crash_label.next_to(crash_site, DOWN, buff=0.2)
        self.add(crash_site, crash_label)

        self.add_subcaption("The NTSB is not a crash investigation agency in the way most people think.", duration=3.0)
        self.add_subcaption("It is a safety recommendation engine that uses crashes as input.", duration=2.5)

        cycle_items = [
            ("Crash", WARNING, crash_site.get_center()),
            ("Go Team", PRIMARY, crash_site.get_center() + np.array([3, 1, 0])),
            ("Investigation", PRIMARY, crash_site.get_center() + np.array([4, -1, 0])),
            ("Findings", ACCENT, crash_site.get_center() + np.array([2, -3, 0])),
            ("Recommendations", ACCENT, crash_site.get_center() + np.array([-1, -3, 0])),
            ("Adoption", SECONDARY, crash_site.get_center() + np.array([-3, -1, 0])),
            ("Safer\nFlights", SECONDARY, crash_site.get_center() + np.array([-2, 1, 0])),
        ]

        cycle_nodes = VGroup()
        cycle_arrows = VGroup()

        for label_text, color, pos in cycle_items:
            if abs(pos[0] - crash_site.get_center()[0]) < 0.01 and abs(pos[1] - crash_site.get_center()[1]) < 0.01:
                continue

            node = Circle(radius=0.4, color=color, fill_opacity=0.2)
            node.move_to(pos)
            label = Text(label_text, font_size=10, color=color, font=MONO)
            if "\n" in label_text:
                label.move_to(node.get_center())
            else:
                label.next_to(node, UP, buff=0.25)
            cycle_nodes.add(VGroup(node, label))

        positions = [item[2] for item in cycle_items]
        for i in range(len(positions)):
            start = positions[i]
            end = positions[(i + 1) % len(positions)]
            arrow = CurvedArrow(start, end, angle=0.3, color=NEUTRAL, stroke_width=1.5)
            cycle_arrows.add(arrow)

        self.play(
            LaggedStart(*[GrowFromCenter(n, run_time=0.5) for n in cycle_nodes], lag_ratio=0.3),
        )
        self.wait(0.5)
        self.play(
            LaggedStart(*[GrowFromPoint(a, a.get_start(), run_time=0.5) for a in cycle_arrows], lag_ratio=0.3),
        )
        self.wait(1.5)

        summary = VGroup(
            Text("Go Team shows up.", font_size=20, color=PRIMARY, font=MONO),
            Text("Party System brings expertise.", font_size=20, color=SECONDARY, font=MONO),
            Text("Report is public.", font_size=20, color=PRIMARY, font=MONO),
            Text("Recommendations get adopted.", font_size=20, color=SECONDARY, font=MONO),
            Text("Next million flights safer.", font_size=20, color=ACCENT, font=MONO),
        )
        summary.arrange(DOWN, buff=0.4, aligned_edge=LEFT)
        summary.to_edge(LEFT, buff=1.0).shift(RIGHT * 0.5)

        self.add_subcaption("The Go Team shows up.", duration=1.0)
        self.add_subcaption("The Party System brings expert knowledge while keeping legal interests out.", duration=3.0)
        self.add_subcaption("The investigation takes a year or two.", duration=1.5)
        self.add_subcaption("The report is public.", duration=1.5)
        self.add_subcaption("The recommendations get adopted.", duration=1.5)
        self.add_subcaption("The next million flights are safer.", duration=2.0)

        self.play(
            LaggedStart(*[FadeIn(line, shift=RIGHT, run_time=0.4) for line in summary], lag_ratio=0.4),
        )
        self.wait(2.0)

        final = Text(
            "It is not perfect.\nIt is not fast.\nBut aviation keeps getting safer.",
            font_size=24, color=PRIMARY, font=MONO,
        )
        final.to_edge(DOWN, buff=0.5)

        self.add_subcaption("It is not perfect. It is not fast.", duration=2.0)
        self.add_subcaption("But it is the reason aviation keeps getting safer.", duration=2.5)
        self.play(Write(final, run_time=2.0))
        self.wait(2.0)

        subscribe_btn = RoundedRectangle(corner_radius=0.2, width=2, height=0.8, color=PRIMARY, stroke_width=2)
        subscribe_text = Text("SUBSCRIBE", font_size=20, color=PRIMARY, font=MONO, weight=BOLD)
        end_screen = Group(subscribe_btn, subscribe_text)
        end_screen.move_to(ORIGIN)

        next_text = Text("Next: A Real NTSB Investigation,\nStep by Step", font_size=16, color=NEUTRAL, font=MONO)
        next_text.next_to(end_screen, DOWN, buff=0.5)

        sources = Text(
            "Sources: NTSB reports | FAA GA Safety Fact Sheet 2025 | @wangtangkiki | @Ecaspu",
            font_size=10, color=NEUTRAL, font=MONO,
        )
        sources.to_edge(DOWN, buff=0.3)

        self.play(
            FadeOut(Group(crash_site, crash_label, cycle_nodes, cycle_arrows, summary, final)),
            run_time=0.8,
        )
        self.play(
            Create(subscribe_btn, run_time=0.5),
            Write(subscribe_text, run_time=0.5),
            Write(next_text, run_time=0.8),
            Write(sources, run_time=0.5),
        )
        self.wait(3.0)

        self.play(FadeOut(Group(subscribe_btn, subscribe_text, next_text, sources)), run_time=0.5)
        self.wait(0.3)
