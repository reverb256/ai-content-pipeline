from manim import *
import numpy as np

# === Color Palette — Classic 3B1B ===
BG = "#1C1C1C"
PRIMARY = "#58C4DD"      # Blue
SECONDARY = "#83C167"    # Green
ACCENT = "#FFFF00"       # Yellow
WARN = "#FF6B6B"         # Red for warnings
MUTED = "#888888"        # Gray
LIGHT = "#EAEAEA"        # Near-white
MONO = "Menlo"

# === Typography Scale ===
TITLE_SZ = 48
HEADING_SZ = 36
BODY_SZ = 28
LABEL_SZ = 22
CAPTION_SZ = 18

# === Scene durations (seconds) — must total ~445.7 to match audio ===
SCENE_DURATIONS = [15, 25, 60, 60, 60, 60, 45, 60, 30, 30]


def make_brain_heatmap(axes, pattern="dense"):
    """Create a fake brain connectivity heatmap on given axes."""
    cells = []
    x_unit = axes.x_length / 8
    y_unit = axes.y_length / 8
    for i in range(8):
        for j in range(8):
            if pattern == "dense":
                val = np.random.uniform(0.6, 1.0)
            elif pattern == "moderate":
                val = np.random.uniform(0.3, 0.7)
            else:  # sparse
                val = np.random.uniform(0.05, 0.35)
            color = interpolate_color(ManimColor(BG), ManimColor(PRIMARY), val)
            cell = Rectangle(
                width=x_unit, height=y_unit,
                fill_color=color, fill_opacity=1, stroke_width=0
            ).move_to(axes.c2p(i-3.5, j-3.5))
            cells.append(cell)
    return VGroup(*cells)


def pad_to_duration(scene, duration):
    """Wait for remaining time so scene lasts exactly `duration` seconds."""
    elapsed = scene.renderer.time
    remaining = duration - elapsed
    if remaining > 0:
        scene.wait(remaining)


# ============================================================
# Scene 1 — The Hook (15s)
# ============================================================
class Scene01_Hook(Scene):
    def construct(self):
        self.camera.background_color = BG
        target = SCENE_DURATIONS[0]

        title = Text("1,372 people.", font_size=TITLE_SZ, color=PRIMARY, weight=BOLD, font=MONO).move_to(UP * 1.5)
        sub1 = Text("AI was wrong 80 percent of the time.", font_size=BODY_SZ, color=LIGHT, font=MONO).next_to(title, DOWN, buff=0.8)
        sub2 = Text("They followed it anyway.", font_size=BODY_SZ, color=WARN, font=MONO).next_to(sub1, DOWN, buff=0.6)

        self.add_subcaption("1,372 people. AI was wrong 80 percent of the time. They followed it anyway.", duration=4)
        self.play(Write(title), run_time=1.2)
        self.play(FadeIn(sub1), run_time=0.8)
        self.play(FadeIn(sub2, shift=DOWN), run_time=0.8)
        self.wait(2.0)

        line = Line(LEFT * 4, RIGHT * 4, color=MUTED, stroke_width=1).next_to(sub2, DOWN, buff=1.2)
        tagline = Text("That is not a bug in human thinking. It is a feature.", font_size=LABEL_SZ, color=MUTED, font=MONO).next_to(line, DOWN, buff=0.6)

        self.add_subcaption("That is not a bug in human thinking. It is a feature. And it is rewiring your brain right now.", duration=4)
        self.play(Create(line), run_time=0.6)
        self.play(Write(tagline), run_time=1.0)
        pad_to_duration(self, target - 0.5)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.5)


# ============================================================
# Scene 2 — The Stakes (25s)
# ============================================================
class Scene02_Stakes(Scene):
    def construct(self):
        self.camera.background_color = BG
        target = SCENE_DURATIONS[1]

        label = Text("COGNITIVE SURRENDER", font_size=TITLE_SZ, color=WARN, weight=BOLD, font=MONO).to_edge(UP, buff=0.8)
        self.add_subcaption("This is cognitive surrender.", duration=2)
        self.play(Write(label), run_time=1.0)
        self.wait(0.5)

        studies = [
            ("Shaw & Nave\nWharton, Jan 2026", "1,372 participants\nPreregistered"),
            ("MIT Media Lab\nJun 2025", "EEG brain scans\n54 participants"),
            ("Frontiers in Psychology\nJul 2026", "N=589\nDependent vs Autonomous"),
        ]

        cards = VGroup()
        for name, detail in studies:
            card = RoundedRectangle(width=3.5, height=1.8, corner_radius=0.1, fill_color="#2A2A2A", fill_opacity=1, stroke_color=PRIMARY, stroke_width=1)
            name_t = Text(name, font_size=LABEL_SZ, color=PRIMARY, font=MONO).move_to(card.get_center() + UP * 0.3)
            detail_t = Text(detail, font_size=CAPTION_SZ, color=MUTED, font=MONO).move_to(card.get_center() + DOWN * 0.4)
            card.add(name_t, detail_t)
            cards.add(card)

        cards.arrange(RIGHT, buff=0.4).move_to(ORIGIN)
        self.add_subcaption("Wharton researchers proved it in January. MIT confirmed it with brain scans in June.", duration=4)
        for i, card in enumerate(cards):
            self.play(FadeIn(card, shift=UP), run_time=0.6)
            self.wait(0.8)

        badge = RoundedRectangle(width=4, height=0.6, corner_radius=0.05, fill_color=SECONDARY, fill_opacity=0.15, stroke_color=SECONDARY, stroke_width=1).to_edge(DOWN, buff=0.8)
        badge_t = Text("RESEARCH-BACKED", font_size=LABEL_SZ, color=SECONDARY, font=MONO).move_to(badge)
        self.add_subcaption("I will show you six mechanisms. All peer-reviewed. All from 2025 or 2026.", duration=3)
        self.play(FadeIn(badge), Write(badge_t), run_time=0.6)
        pad_to_duration(self, target - 0.5)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.5)


# ============================================================
# Scene 3 — The Offloading Spectrum (60s)
# ============================================================
class Scene03_OffloadingSpectrum(Scene):
    def construct(self):
        self.camera.background_color = BG
        target = SCENE_DURATIONS[2]

        title = Text("The Offloading Spectrum", font_size=HEADING_SZ, color=PRIMARY, weight=BOLD, font=MONO).to_edge(UP, buff=0.6)
        self.add_subcaption("Not all AI use is equal. That is the finding nobody expected.", duration=3)
        self.play(Write(title), run_time=0.8)
        self.wait(0.5)

        left_box = Rectangle(width=5.5, height=4, fill_color="#1A1A1A", fill_opacity=1, stroke_color=WARN, stroke_width=1).shift(LEFT * 3.2)
        right_box = Rectangle(width=5.5, height=4, fill_color="#1A1A1A", fill_opacity=1, stroke_color=SECONDARY, stroke_width=1).shift(RIGHT * 3.2)

        left_label = Text("DEPENDENT", font_size=LABEL_SZ, color=WARN, font=MONO).move_to(left_box.get_top() + DOWN * 0.4)
        right_label = Text("AUTONOMOUS", font_size=LABEL_SZ, color=SECONDARY, font=MONO).move_to(right_box.get_top() + DOWN * 0.4)

        left_person = Text("You", font_size=BODY_SZ, color=LIGHT, font=MONO).move_to(left_box.get_center() + UP * 0.5)
        left_ai = Rectangle(width=2, height=0.4, fill_color=PRIMARY, fill_opacity=0.3).move_to(left_box.get_center() + DOWN * 0.3)
        left_ai_t = Text("AI output", font_size=CAPTION_SZ, color=PRIMARY, font=MONO).move_to(left_ai)
        left_result = Text("Copy → Paste", font_size=CAPTION_SZ, color=WARN, font=MONO).move_to(left_box.get_center() + DOWN * 1.3)

        right_person = Text("You", font_size=BODY_SZ, color=LIGHT, font=MONO).move_to(right_box.get_center() + UP * 0.5)
        right_ai = Rectangle(width=2, height=0.4, fill_color=SECONDARY, fill_opacity=0.3).move_to(right_box.get_center() + DOWN * 0.3)
        right_ai_t = Text("AI scaffold", font_size=CAPTION_SZ, color=SECONDARY, font=MONO).move_to(right_ai)
        right_result = Text("Think → Rewrite", font_size=CAPTION_SZ, color=SECONDARY, font=MONO).move_to(right_box.get_center() + DOWN * 1.3)

        self.add_subcaption("Two modes: dependent offloading and autonomous offloading.", duration=3)
        self.play(Create(left_box), Create(right_box), run_time=0.6)
        self.play(Write(left_label), Write(right_label), run_time=0.5)
        self.wait(0.3)
        self.play(Write(left_person), Write(right_person), run_time=0.5)
        self.play(FadeIn(left_ai), Write(left_ai_t), run_time=0.5)
        self.play(FadeIn(right_ai), Write(right_ai_t), run_time=0.5)
        self.play(Write(left_result), Write(right_result), run_time=0.5)
        self.wait(2.0)

        self.add_subcaption("Both feel equal in the moment. But downstream correlates diverge sharply.", duration=4)
        axes = Axes(x_range=[0, 3, 1], y_range=[0, 10, 2], x_length=6, y_length=2.5,
                    axis_config={"color": MUTED, "include_tip": False}).to_edge(DOWN, buff=0.5)
        x_labels = VGroup(
            Text("Now", font_size=CAPTION_SZ, color=MUTED, font=MONO).move_to(axes.c2p(0.5, -0.8)),
            Text("3 mo", font_size=CAPTION_SZ, color=MUTED, font=MONO).move_to(axes.c2p(2.5, -0.8)),
        )

        line_dep = axes.plot(lambda x: 8 - 2.5 * x, x_range=[0, 3], color=WARN, stroke_width=2)
        line_auto = axes.plot(lambda x: 8 - 0.3 * x, x_range=[0, 3], color=SECONDARY, stroke_width=2)
        dep_label = Text("Dependent", font_size=CAPTION_SZ, color=WARN, font=MONO).move_to(axes.c2p(2.8, 2.5))
        auto_label = Text("Autonomous", font_size=CAPTION_SZ, color=SECONDARY, font=MONO).move_to(axes.c2p(2.8, 7.5))

        self.play(Create(axes), Write(x_labels), run_time=0.6)
        self.play(Create(line_dep), Create(line_auto), run_time=1.0)
        self.play(Write(dep_label), Write(auto_label), run_time=0.5)
        self.wait(3.0)

        cite = Text("Frontiers in Psychology, Jul 16 2026  |  DOI: 10.3389/fpsyg.2026.1878629", font_size=CAPTION_SZ, color=MUTED, font=MONO).to_edge(DOWN, buff=0.15)
        self.add_subcaption("The takeaway: you cannot trust your own judgment of whether AI is helping you.", duration=3)
        self.play(Write(cite), run_time=0.5)
        pad_to_duration(self, target - 0.5)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.5)


# ============================================================
# Scene 4 — Cognitive Surrender (60s)
# ============================================================
class Scene04_CognitiveSurrender(Scene):
    def construct(self):
        self.camera.background_color = BG
        target = SCENE_DURATIONS[3]

        title = Text("Cognitive Surrender", font_size=HEADING_SZ, color=WARN, weight=BOLD, font=MONO).to_edge(UP, buff=0.6)
        self.add_subcaption("Now the finding that should keep you up at night.", duration=2)
        self.play(Write(title), run_time=0.8)
        self.wait(0.3)

        flow_y = 0.5
        box_w, box_h = 2.2, 0.7

        b1 = Rectangle(width=box_w, height=box_h, fill_color="#2A2A2A", fill_opacity=1, stroke_color=PRIMARY, stroke_width=1).shift(LEFT * 5)
        t1 = Text("Question", font_size=LABEL_SZ, color=PRIMARY, font=MONO).move_to(b1)

        b2 = Rectangle(width=box_w, height=box_h, fill_color="#2A2A2A", fill_opacity=1, stroke_color=WARN, stroke_width=1)
        t2 = Text("AI Answer", font_size=LABEL_SZ, color=WARN, font=MONO).move_to(b2)
        x_mark = Text("X", font_size=18, color=WARN, font=MONO).next_to(b2, RIGHT, buff=0.1)

        b3 = Rectangle(width=box_w, height=box_h, fill_color="#2A2A2A", fill_opacity=1, stroke_color=MUTED, stroke_width=1).shift(RIGHT * 5)
        t3 = Text("Accept", font_size=LABEL_SZ, color=MUTED, font=MONO).move_to(b3)

        arrows = VGroup(
            Arrow(b1.get_right(), b2.get_left(), color=PRIMARY, buff=0.1),
            Arrow(b2.get_right(), b3.get_left(), color=WARN, buff=0.1),
        )

        self.add_subcaption("1,372 participants. AI was deliberately wrong 80 percent of the time.", duration=4)
        self.play(Create(b1), Write(t1), run_time=0.5)
        self.play(Create(arrows[0]), Create(b2), Write(t2), Write(x_mark), run_time=0.5)
        self.play(Create(arrows[1]), Create(b3), Write(t3), run_time=0.5)
        self.wait(2.0)

        stats_y = -1.5
        stat1 = Text("Trials with AI: 52%", font_size=BODY_SZ, color=LIGHT, font=MONO).shift(LEFT * 3 + DOWN * stats_y)
        stat2 = Text("Followed faulty AI: 80%", font_size=BODY_SZ, color=WARN, font=MONO).shift(RIGHT * 0 + DOWN * stats_y)
        stat3 = Text("Cohen's h = 0.81", font_size=BODY_SZ, color=ACCENT, font=MONO).shift(RIGHT * 3.5 + DOWN * stats_y)

        self.add_subcaption("Participants followed faulty AI approximately 80 percent of the time. Cohen's h equals 0.81.", duration=5)
        self.play(Write(stat1), run_time=0.6)
        self.play(Write(stat2), run_time=0.6)
        self.play(Write(stat3), run_time=0.6)

        large_label = Text("LARGE EFFECT", font_size=LABEL_SZ, color=WARN, weight=BOLD, font=MONO).next_to(stat3, DOWN, buff=0.4)
        self.play(Write(large_label), run_time=0.5)
        self.wait(3.0)

        cite = Text("Shaw & Nave, Wharton  |  PsyArXiv, Jan 12 2026", font_size=CAPTION_SZ, color=MUTED, font=MONO).to_edge(DOWN, buff=0.2)
        self.play(Write(cite), run_time=0.4)
        pad_to_duration(self, target - 0.5)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.5)


# ============================================================
# Scene 5 — The Brain Evidence (60s)
# ============================================================
class Scene05_BrainEvidence(Scene):
    def construct(self):
        self.camera.background_color = BG
        target = SCENE_DURATIONS[4]

        title = Text("The Brain Evidence", font_size=HEADING_SZ, color=PRIMARY, weight=BOLD, font=MONO).to_edge(UP, buff=0.6)
        self.add_subcaption("You might think: I would never follow wrong AI advice. The brain data says otherwise.", duration=3)
        self.play(Write(title), run_time=0.8)
        self.wait(0.3)

        brain_labels = ["Brain-only", "Search", "LLM"]
        brain_patterns = ["dense", "moderate", "sparse"]
        brain_colors = [SECONDARY, ACCENT, WARN]

        brains = VGroup()
        for i, (lbl, pat, col) in enumerate(zip(brain_labels, brain_patterns, brain_colors)):
            ax = Axes(x_range=[0, 8, 1], y_range=[0, 8, 1], x_length=2, y_length=2,
                      axis_config={"color": MUTED, "include_tip": False}).shift(LEFT * 6 + RIGHT * 3.5 * i + DOWN * 0.3)
            heatmap = make_brain_heatmap(ax, pat)
            label = Text(lbl, font_size=LABEL_SZ, color=col, font=MONO).move_to(ax.get_bottom() + DOWN * 0.5)
            brains.add(VGroup(ax, heatmap, label))

        self.add_subcaption("MIT EEG study: 54 participants. Three conditions. Brain-only, Search, LLM.", duration=4)
        for b in brains:
            self.play(Create(b[0]), Create(b[1]), Write(b[2]), run_time=0.5)
            self.wait(0.5)

        self.add_subcaption("In session four, LLM users switched to brain-only. Connectivity remained under-engaged.", duration=4)
        ax4 = Axes(x_range=[0, 8, 1], y_range=[0, 8, 1], x_length=2, y_length=2,
                   axis_config={"color": MUTED, "include_tip": False}).shift(RIGHT * 6 + DOWN * 0.3)
        heatmap4 = make_brain_heatmap(ax4, "sparse")
        label4 = Text("LLM->Brain", font_size=LABEL_SZ, color=WARN, font=MONO).move_to(ax4.get_bottom() + DOWN * 0.5)
        debt_label = Text("Cognitive debt", font_size=CAPTION_SZ, color=WARN, font=MONO).next_to(label4, DOWN, buff=0.2)

        self.play(Create(ax4), Create(heatmap4), Write(label4), run_time=0.5)
        self.play(Write(debt_label), run_time=0.4)
        self.wait(2.0)

        self.add_subcaption("LLM users struggled to quote their own essays minutes later. The words did not feel like theirs.", duration=3)
        bar_axes = Axes(x_range=[0, 3, 1], y_range=[0, 10, 2], x_length=4, y_length=2,
                        axis_config={"color": MUTED, "include_tip": False}).to_edge(DOWN, buff=0.8)
        bars = VGroup(
            Rectangle(width=0.6, height=8, fill_color=SECONDARY, fill_opacity=0.8, stroke_width=0).move_to(bar_axes.c2p(0.5, 4)),
            Rectangle(width=0.6, height=5, fill_color=ACCENT, fill_opacity=0.8, stroke_width=0).move_to(bar_axes.c2p(1.5, 2.5)),
            Rectangle(width=0.6, height=2.5, fill_color=WARN, fill_opacity=0.8, stroke_width=0).move_to(bar_axes.c2p(2.5, 1.25)),
        )
        bar_labels = VGroup(
            Text("Brain", font_size=CAPTION_SZ, color=MUTED, font=MONO).move_to(bar_axes.c2p(0.5, -0.6)),
            Text("Search", font_size=CAPTION_SZ, color=MUTED, font=MONO).move_to(bar_axes.c2p(1.5, -0.6)),
            Text("LLM", font_size=CAPTION_SZ, color=MUTED, font=MONO).move_to(bar_axes.c2p(2.5, -0.6)),
        )
        y_label = Text("Ownership", font_size=CAPTION_SZ, color=MUTED, font=MONO).rotate(PI/2).next_to(bar_axes, LEFT, buff=0.3)

        self.play(Create(bar_axes), Write(bar_labels), Write(y_label), run_time=0.5)
        for bar in bars:
            self.play(GrowFromEdge(bar, DOWN), run_time=0.4)
        self.wait(2.0)

        cite = Text("MIT Media Lab  |  arXiv:2506.08872  |  115+ citations", font_size=CAPTION_SZ, color=MUTED, font=MONO).to_edge(DOWN, buff=0.1)
        self.play(Write(cite), run_time=0.4)
        pad_to_duration(self, target - 0.5)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.5)


# ============================================================
# Scene 6 — The Theory (60s)
# ============================================================
class Scene06_Theory(Scene):
    def construct(self):
        self.camera.background_color = BG
        target = SCENE_DURATIONS[5]

        title = Text("Generative Capacity Erosion Hypothesis", font_size=HEADING_SZ - 4, color=PRIMARY, weight=BOLD, font=MONO).to_edge(UP, buff=0.5)
        self.add_subcaption("Is this temporary? Or permanent? The first formal theory of what AI does to human creativity over time.", duration=4)
        self.play(Write(title), run_time=0.8)
        self.wait(0.3)

        mechanisms = [
            ("1", "Cognitive Muscle\nAtrophy", "Neural circuits\nyou don't use,\nyou lose", WARN),
            ("2", "Ambiguity\nTolerance Erosion", "AI resolves\nuncertainty\ninstantly", ACCENT),
            ("3", "Self-Efficacy\nDisplacement", "You stop trusting\nyour own ideas", PRIMARY),
            ("4", "Evaluative\nCapacity Atrophy", "You lose ability\nto judge good\nfrom bad", SECONDARY),
        ]

        panels = VGroup()
        for num, name, desc, col in mechanisms:
            panel = RoundedRectangle(width=2.8, height=2.2, corner_radius=0.08, fill_color="#1E1E1E", fill_opacity=1, stroke_color=col, stroke_width=1)
            num_t = Text(num, font_size=24, color=col, weight=BOLD, font=MONO).move_to(panel.get_top() + LEFT * 1.1 + DOWN * 0.3)
            name_t = Text(name, font_size=LABEL_SZ, color=col, font=MONO).move_to(panel.get_center() + UP * 0.2)
            desc_t = Text(desc, font_size=CAPTION_SZ, color=MUTED, font=MONO).move_to(panel.get_center() + DOWN * 0.5)
            panel.add(num_t, name_t, desc_t)
            panels.add(panel)

        panels.arrange_in_grid(rows=2, cols=2, buff=0.3).move_to(ORIGIN, DOWN * 0.2)
        self.add_subcaption("Four mechanisms: cognitive muscle atrophy, ambiguity tolerance erosion, self-efficacy displacement, evaluative capacity atrophy.", duration=6)
        for panel in panels:
            self.play(FadeIn(panel), run_time=0.5)
            self.wait(0.5)

        self.add_subcaption("Calculators augmented arithmetic. GPS augmented navigation. AI substitutes for core cognitive processes.", duration=4)
        comp_y = -3.2
        calc_box = RoundedRectangle(width=3, height=0.8, corner_radius=0.05, fill_color="#1A1A1A", fill_opacity=1, stroke_color=SECONDARY, stroke_width=1).shift(LEFT * 3.5 + DOWN * comp_y)
        calc_t = Text("Calculator: augments skill", font_size=LABEL_SZ, color=SECONDARY, font=MONO).move_to(calc_box)
        ai_box = RoundedRectangle(width=3, height=0.8, corner_radius=0.05, fill_color="#1A1A1A", fill_opacity=1, stroke_color=WARN, stroke_width=1).shift(RIGHT * 3.5 + DOWN * comp_y)
        ai_t = Text("AI: substitutes process", font_size=LABEL_SZ, color=WARN, font=MONO).move_to(ai_box)

        self.play(Create(calc_box), Write(calc_t), run_time=0.5)
        self.play(Create(ai_box), Write(ai_t), run_time=0.5)
        self.wait(2.0)

        cite = Text("Gupta & Shabista  |  AAAI Symposium, May 18 2026", font_size=CAPTION_SZ, color=MUTED, font=MONO).to_edge(DOWN, buff=0.15)
        self.play(Write(cite), run_time=0.4)
        pad_to_duration(self, target - 0.5)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.5)


# ============================================================
# Scene 7 — The Moderator (45s)
# ============================================================
class Scene07_Moderator(Scene):
    def construct(self):
        self.camera.background_color = BG
        target = SCENE_DURATIONS[6]

        title = Text("The Moderator: Metacognition", font_size=HEADING_SZ - 4, color=PRIMARY, weight=BOLD, font=MONO).to_edge(UP, buff=0.5)
        self.add_subcaption("So is everyone doomed? No. The research points to one key difference. Metacognition.", duration=3)
        self.play(Write(title), run_time=0.8)
        self.wait(0.3)

        axes = Axes(x_range=[0, 10, 2], y_range=[0, 10, 2], x_length=6, y_length=4,
                    axis_config={"color": MUTED, "include_tip": False}).shift(DOWN * 0.3)
        x_label = Text("Metacognitive skill", font_size=LABEL_SZ, color=MUTED, font=MONO).move_to(axes.x_axis.get_bottom() + DOWN * 0.6)
        y_label = Text("AI benefit", font_size=LABEL_SZ, color=MUTED, font=MONO).rotate(PI/2).next_to(axes.y_axis, LEFT, buff=0.4)

        line = axes.plot(lambda x: 1.5 + 0.7 * x, x_range=[1, 9], color=PRIMARY, stroke_width=2)

        np.random.seed(42)
        dots_high = VGroup(*[
            Dot(axes.c2p(x, y), color=SECONDARY, radius=0.06)
            for x, y in zip(np.random.uniform(6, 9.5, 15), np.random.uniform(6, 9.5, 15))
        ])
        dots_low = VGroup(*[
            Dot(axes.c2p(x, y), color=WARN, radius=0.06)
            for x, y in zip(np.random.uniform(1, 5, 12), np.random.uniform(1, 5, 12))
        ])

        self.add_subcaption("For people who think about how they think, AI is a lever. For everyone else, it is a crutch.", duration=4)
        self.play(Create(axes), Write(x_label), Write(y_label), run_time=0.6)
        self.play(Create(line), run_time=0.8)
        for dot in dots_high:
            self.add(dot)
        for dot in dots_low:
            self.add(dot)
        self.play(FadeIn(dots_high), FadeIn(dots_low), run_time=0.6)

        high_label = Text("Deliberate users", font_size=LABEL_SZ, color=SECONDARY, font=MONO).move_to(axes.c2p(8, 9))
        low_label = Text("Autopilot users", font_size=LABEL_SZ, color=WARN, font=MONO).move_to(axes.c2p(2, 2))
        self.play(Write(high_label), Write(low_label), run_time=0.5)
        self.wait(3.0)

        self.add_subcaption("This is the individual difference that matters. Not age. Not education. Metacognition.", duration=3)
        takeaway = Text("Metacognition is the moderator.", font_size=BODY_SZ, color=ACCENT, font=MONO).to_edge(DOWN, buff=0.8)
        self.play(Write(takeaway), run_time=0.6)
        pad_to_duration(self, target - 0.5)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.5)


# ============================================================
# Scene 8 — Structural Asymmetry (60s)
# ============================================================
class Scene08_StructuralAsymmetry(Scene):
    def construct(self):
        self.camera.background_color = BG
        target = SCENE_DURATIONS[7]

        title = Text("Structural Asymmetry", font_size=HEADING_SZ, color=PRIMARY, weight=BOLD, font=MONO).to_edge(UP, buff=0.5)
        self.add_subcaption("Why is this happening now? Why not with calculators? Why not with search engines?", duration=3)
        self.play(Write(title), run_time=0.8)
        self.wait(0.3)

        left_col = Rectangle(width=4.5, height=4.5, fill_color="#1A1A1A", fill_opacity=1, stroke_color=MUTED, stroke_width=1).shift(LEFT * 3.5)
        right_col = Rectangle(width=4.5, height=4.5, fill_color="#1A1A1A", fill_opacity=1, stroke_color=WARN, stroke_width=1).shift(RIGHT * 3.5)

        left_title = Text("Human\nRelationship", font_size=LABEL_SZ, color=MUTED, font=MONO).move_to(left_col.get_top() + DOWN * 0.5)
        right_title = Text("AI\nRelationship", font_size=LABEL_SZ, color=WARN, font=MONO).move_to(right_col.get_top() + DOWN * 0.5)

        left_items = VGroup(*[
            Text(t, font_size=LABEL_SZ - 2, color=LIGHT, font=MONO)
            for t in ["Mutual needs", "Friction", "Limits", "Ego", "Reciprocity"]
        ]).arrange(DOWN, buff=0.3).move_to(left_col.get_center() + DOWN * 0.3)

        right_items = VGroup(*[
            Text(t, font_size=LABEL_SZ - 2, color=WARN, font=MONO)
            for t in ["One-way", "No friction", "No limits", "No ego", "Asks for data"]
        ]).arrange(DOWN, buff=0.3).move_to(right_col.get_center() + DOWN * 0.3)

        self.add_subcaption("No prior relationship has this shape. Tools do not talk back. People have egos, needs, limits. AI has none of these.", duration=5)
        self.play(Create(left_col), Create(right_col), run_time=0.5)
        self.play(Write(left_title), Write(right_title), run_time=0.4)
        for li, ri in zip(left_items, right_items):
            self.play(Write(li), Write(ri), run_time=0.3)
        self.wait(2.0)

        asym_arrow = Arrow(left_col.get_right() + UP * 1.5, right_col.get_left() + UP * 1.5, color=ACCENT, buff=0.1, stroke_width=3)
        asym_label = Text("Structural\nasymmetry", font_size=CAPTION_SZ, color=ACCENT, font=MONO).move_to(asym_arrow.get_center() + UP * 0.4)
        self.play(Create(asym_arrow), Write(asym_label), run_time=0.5)
        self.wait(2.0)

        self.add_subcaption("The Anthropic 81,000-person study confirms this. The dominant request: Give me my life back.", duration=3)
        anthropic_box = RoundedRectangle(width=6, height=0.8, corner_radius=0.05, fill_color="#2A2A2A", fill_opacity=1, stroke_color=PRIMARY, stroke_width=1).to_edge(DOWN, buff=0.6)
        anthropic_t = Text('Anthropic 81k: "Give me my life back"', font_size=LABEL_SZ, color=PRIMARY, font=MONO).move_to(anthropic_box)
        self.play(FadeIn(anthropic_box), Write(anthropic_t), run_time=0.5)
        pad_to_duration(self, target - 0.5)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.5)


# ============================================================
# Scene 9 — The Payoff (30s)
# ============================================================
class Scene09_Payoff(Scene):
    def construct(self):
        self.camera.background_color = BG
        target = SCENE_DURATIONS[8]

        studies = [
            "Shaw & Nave\nWharton 2026", "MIT Media Lab\n2025", "Frontiers\nPsychology 2026",
            "AAAI\nGCEH 2026", "APA Monitor\n2026", "TIME\nApr 2026",
        ]

        cards = VGroup()
        for s in studies:
            card = RoundedRectangle(width=2.5, height=1.2, corner_radius=0.06, fill_color="#1E1E1E", fill_opacity=1, stroke_color=PRIMARY, stroke_width=1)
            t = Text(s, font_size=CAPTION_SZ, color=PRIMARY, font=MONO).move_to(card)
            card.add(t)
            cards.add(card)

        cards.arrange_in_grid(rows=2, cols=3, buff=0.25).move_to(UP * 1.2)
        self.add_subcaption("Six mechanisms. All peer-reviewed. All from the last eighteen months.", duration=4)
        for card in cards:
            self.play(FadeIn(card), run_time=0.3)
        self.wait(2.0)

        self.add_subcaption("The question is not whether AI will change your thinking. It already has. The question is whether you will notice.", duration=4)
        question = Text("Are you using AI —\nor is AI using you?", font_size=HEADING_SZ, color=ACCENT, weight=BOLD, font=MONO).move_to(DOWN * 1.5)
        self.play(cards.animate.set_opacity(0.3), run_time=0.8)
        self.play(Write(question), run_time=1.0)
        pad_to_duration(self, target - 0.5)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.5)


# ============================================================
# Scene 10 — The Close (30s)
# ============================================================
class Scene10_Close(Scene):
    def construct(self):
        self.camera.background_color = BG
        target = SCENE_DURATIONS[9]

        title = Text("The Cognitive Offloading Crisis", font_size=HEADING_SZ, color=PRIMARY, weight=BOLD, font=MONO).move_to(UP * 1.5)
        subtitle = Text("Applied Psychology in the AI Era", font_size=LABEL_SZ, color=MUTED, font=MONO).next_to(title, DOWN, buff=0.5)

        self.add_subcaption("I will link every study in the description. Read the Frontiers paper.", duration=3)
        self.play(Write(title), run_time=0.8)
        self.play(Write(subtitle), run_time=0.5)
        self.wait(0.5)

        sub_btn = RoundedRectangle(width=2.5, height=0.7, corner_radius=0.05, fill_color=WARN, fill_opacity=1, stroke_width=0).move_to(DOWN * 0.5)
        sub_t = Text("SUBSCRIBE", font_size=LABEL_SZ, color=BG, weight=BOLD, font=MONO).move_to(sub_btn)
        self.add_subcaption("If you want more research-backed breakdowns of what AI is actually doing to us, subscribe.", duration=3)
        self.play(FadeIn(sub_btn), Write(sub_t), run_time=0.5)
        self.wait(0.5)
        self.play(sub_btn.animate.scale(1.05), rate_func=there_and_back, run_time=0.6)

        next_box = RoundedRectangle(width=4, height=0.8, corner_radius=0.05, fill_color="#1E1E1E", fill_opacity=1, stroke_color=SECONDARY, stroke_width=1).move_to(DOWN * 1.8)
        next_t = Text("Next: The Metacognition Test", font_size=LABEL_SZ, color=SECONDARY, font=MONO).move_to(next_box)
        self.add_subcaption("Next week: the metacognition test that predicts whether AI helps or hurts you.", duration=3)
        self.play(FadeIn(next_box), Write(next_t), run_time=0.5)
        pad_to_duration(self, target - 0.5)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.5)
