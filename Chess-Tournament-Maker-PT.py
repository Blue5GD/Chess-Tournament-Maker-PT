import tkinter as tk
import customtkinter as ctk
from tkinter import filedialog, messagebox
import json
import random
import os

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class Player:
    # Represents a single player in the tournament.
    def __init__(self, name, school, is_active=True, score=0.0, opponent_history=None,
                 color_history=None, absent_count=0, had_pairing_bye=False, round_joined=1):
        self.name = name
        self.school = school
        self.is_active = is_active
        self.score = score
        # Initialize lists to avoid mutable default argument issues
        self.opponent_history = opponent_history if opponent_history is not None else []
        self.color_history = color_history if color_history is not None else []
        self.absent_count = absent_count
        self.had_pairing_bye = had_pairing_bye
        self.round_joined = round_joined

    def to_dict(self):
        # Converts player object's attributes into a dictionary for JSON serialization.
        return self.__dict__

    @classmethod
    def from_dict(cls, data):
        # Creates a Player object from a dictionary.
        return cls(**data)

    def __repr__(self):
        return f"Player({self.name}, {self.school}, Score: {self.score})"

class TournamentApp(ctk.CTk):
    # The main application class for the Chess Club Tournament Manager GUI.
    def __init__(self):
        super().__init__()

        self.title("Chess Club Tournament Manager")
        self.geometry("1200x850")

        self.players = []
        self.current_round = 1
        self.filename = None
        self.pairings_data = {} # Stores pairings for the current round

        self.unsaved_changes = False # Flag to track unsaved modifications

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.tabview = ctk.CTkTabview(self, width=250)
        self.tabview.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        self.tabview.add("Player Management")
        self.tabview.add("Tournament")
        self.tabview.add("Help & Rules")

        self.create_player_management_tab()
        self.create_tournament_tab()
        self.create_help_tab()

        self.result_widgets = {} # Stores UI widgets for result entry for the current round
        self.selected_player = None
        self.selected_button = None

        self.protocol("WM_DELETE_WINDOW", self.on_closing) # Intercept window close event
        self.update_tournament_button_states() # Set initial state of tournament buttons

    def create_player_management_tab(self):
        # Sets up the 'Player Management' tab with widgets for adding, managing, and importing/exporting player data.
        pm_tab = self.tabview.tab("Player Management")
        pm_tab.grid_columnconfigure(1, weight=1)
        pm_tab.grid_rowconfigure(0, weight=1)

        left_frame = ctk.CTkFrame(pm_tab, width=280)
        left_frame.grid(row=0, column=0, padx=(0, 20), sticky="ns")
        left_frame.grid_propagate(False)

        add_player_frame = ctk.CTkFrame(left_frame)
        add_player_frame.pack(pady=20, padx=20, fill="x")
        ctk.CTkLabel(add_player_frame, text="Add New Player", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(0,10))
        self.player_name_entry = ctk.CTkEntry(add_player_frame, placeholder_text="Player Name")
        self.player_name_entry.pack(pady=5, fill="x")
        self.school_var = tk.StringVar(value="Middle School") # Variable for school type radio buttons

        ctk.CTkRadioButton(add_player_frame, text="Middle School", variable=self.school_var, value="Middle School").pack(anchor="w", padx=10, pady=2)
        ctk.CTkRadioButton(add_player_frame, text="High School", variable=self.school_var, value="High School").pack(anchor="w", padx=10, pady=2)
        ctk.CTkButton(add_player_frame, text="Add Player", command=self.add_player).pack(pady=10, fill="x")

        manage_frame = ctk.CTkFrame(left_frame)
        manage_frame.pack(pady=20, padx=20, fill="x")
        ctk.CTkLabel(manage_frame, text="Manage Selected Player", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(0,10))
        ctk.CTkButton(manage_frame, text="Set as INACTIVE", command=self.set_player_status_inactive).pack(pady=5, fill="x")
        ctk.CTkButton(manage_frame, text="Set as ACTIVE", command=self.set_player_status_active).pack(pady=5, fill="x")
        ctk.CTkButton(manage_frame, text="Delete Player", fg_color="#D32F2F", hover_color="#B71C1C", command=self.delete_player).pack(pady=5, fill="x")

        file_frame = ctk.CTkFrame(left_frame)
        file_frame.pack(pady=20, padx=20, fill="x")
        ctk.CTkLabel(file_frame, text="File Operations", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(0,10))
        ctk.CTkButton(file_frame, text="Import Tournament (.json)", command=self.import_data).pack(pady=5, fill="x")
        ctk.CTkButton(file_frame, text="Export Tournament (.json)", command=self.export_data).pack(pady=5, fill="x")

        player_list_frame = ctk.CTkFrame(pm_tab)
        player_list_frame.grid(row=0, column=1, sticky="nsew")
        ctk.CTkLabel(player_list_frame, text="Current Player Roster", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        self.player_scroll_frame = ctk.CTkScrollableFrame(player_list_frame)
        self.player_scroll_frame.pack(expand=True, fill="both", padx=10, pady=10)

    def create_tournament_tab(self):
        # Sets up the 'Tournament' tab with controls for generating pairings, submitting results, and displaying match information.
        self.tourney_tab = self.tabview.tab("Tournament")
        self.tourney_tab.grid_columnconfigure(0, weight=1)
        self.tourney_tab.grid_rowconfigure(1, weight=1)

        control_frame = ctk.CTkFrame(self.tourney_tab)
        control_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        self.round_label = ctk.CTkLabel(control_frame, text=f"Current Round: {self.current_round}", font=ctk.CTkFont(size=16, weight="bold"))
        self.round_label.pack(side="left", padx=20)

        self.submit_results_button = ctk.CTkButton(control_frame, text="Submit Results & Finalize Round", command=self.submit_results)
        self.submit_results_button.pack(side="right", padx=10)
        self.generate_pairings_button = ctk.CTkButton(control_frame, text="Generate Pairings for Next Round", command=self.generate_pairings_for_round)
        self.generate_pairings_button.pack(side="right", padx=10)

        self.tourney_display_container = ctk.CTkFrame(self.tourney_tab, fg_color="transparent")
        self.tourney_display_container.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.tourney_display_container.grid_columnconfigure(0, weight=1)
        self.tourney_display_container.grid_columnconfigure(1, weight=1)
        self.tourney_display_container.grid_rowconfigure(0, weight=1)
        self._build_tournament_display()

    def _build_tournament_display(self):
        # Creates the UI elements for displaying pairings and entering results for both Middle School and High School brackets.
        ms_container = ctk.CTkFrame(self.tourney_display_container)
        ms_container.grid(row=0, column=0, padx=(0, 5), pady=0, sticky="nsew")
        ms_container.grid_rowconfigure(1, weight=1); ms_container.grid_rowconfigure(2, weight=2)
        ms_container.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(ms_container, text="Middle School Bracket", font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, pady=5)
        self.ms_results_textbox = ctk.CTkTextbox(ms_container, wrap="word", font=("Courier New", 12))
        self.ms_results_textbox.grid(row=1, column=0, sticky="nsew", padx=5, pady=(0,5))
        self.ms_results_textbox.configure(state="disabled")
        self.ms_results_frame = ctk.CTkScrollableFrame(ms_container, label_text="Enter Results")
        self.ms_results_frame.grid(row=2, column=0, sticky="nsew", padx=5, pady=(5,5))

        hs_container = ctk.CTkFrame(self.tourney_display_container)
        hs_container.grid(row=0, column=1, padx=(5, 0), pady=0, sticky="nsew")
        hs_container.grid_rowconfigure(1, weight=1); hs_container.grid_rowconfigure(2, weight=2)
        hs_container.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(hs_container, text="High School Bracket", font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, pady=5)
        self.hs_results_textbox = ctk.CTkTextbox(hs_container, wrap="word", font=("Courier New", 12))
        self.hs_results_textbox.grid(row=1, column=0, sticky="nsew", padx=5, pady=(0,5))
        self.hs_results_textbox.configure(state="disabled")
        self.hs_results_frame = ctk.CTkScrollableFrame(hs_container, label_text="Enter Results")
        self.hs_results_frame.grid(row=2, column=0, sticky="nsew", padx=5, pady=(5,5))

    def create_help_tab(self):
        # Sets up the Help & Rules tab with a read-only text box containing instructions and tournament rules.
        help_tab = self.tabview.tab("Help & Rules")
        help_tab.grid_columnconfigure(0, weight=1)
        help_tab.grid_rowconfigure(0, weight=1)
        help_textbox = ctk.CTkTextbox(help_tab, wrap="word", font=("Segoe UI", 13))
        help_textbox.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        help_content = """
# --- HOW TO USE THE PROGRAM ---

# 1.  Player Management Tab:
#     - Add Players: Enter a player's name, select their school (Middle/High), and click "Add Player". New players can be added at any time.
#     - Manage Players: Select a player from the list on the right. You can then mark them as "Inactive" (if they leave the club) or "Active". Inactive players will automatically receive absent byes and will not be present in any newly generated pairings.
#     - Import/Export: Use the buttons to save your current tournament progress to a .json file or load a previous tournament. ALWAYS export your progress when you are done.

# 2.  Tournament Tab:
#     - Generate Pairings: Once players are added, click "Generate Pairings for Next Round". This will use the pairing logic to create matches for both brackets.
#     - View Pairings & Enter Results: The pairings will appear in the text boxes. You can copy this text to a Google Doc. Below the pairings, controls will appear to enter results.
#     - Mark Absences: For players who did not show up, check the "Absent" box next to their name.
#     - Submit Results: After setting all results (Win/Loss/Draw) and marking any absences, click "Submit Results & Finalize Round". This will calculate scores, update player histories, and prepare for the next round.

# --- PAIRING LOGIC PRIORITY ---

# The program uses a Swiss-style pairing system with the following priorities:

# 1.  Score Matching: Players are primarily paired against others in the same score group. The system works down from the top score.
# 2.  Opponent History: The system prioritizes pairing players who have NOT played each other before. If no such pairing is possible, it will allow a rematch and favor opponents played least often or least recently.
# 3.  Color Balancing: The system tries to give players the color they have played less. If they have played an equal number of games as White and Black, it will try to alternate from their last game.
# 4.  Randomness: If multiple opponents are equally valid after the above rules, one is chosen randomly.

# --- SCORING AND RULES ---

# -   Win: 1.0 point
# -   Draw: 0.5 points
# -   Loss: 0.0 points
# -   Pairing Bye: 1.0 point. This happens when there is an odd number of players. A player cannot receive a pairing bye two rounds in a row.
# -   Absent Bye: 0.5 points. This is awarded when a player is marked "Absent". A player will only receive points for their first THREE absences. After that, absences are worth 0 points.
# -   Inactive Players: Automatically receive absent byes each round.
        """
        help_textbox.insert("1.0", help_content)
        help_textbox.configure(state="disabled")

    def add_player(self):
        # Adds a new player to the tournament roster based on input fields.
        name = self.player_name_entry.get().strip()
        school = self.school_var.get()
        if not name:
            messagebox.showerror("Error", "Player name cannot be empty.")
            return
        if any(p.name.lower() == name.lower() for p in self.players):
            messagebox.showerror("Error", "A player with this name already exists.")
            return
        new_player = Player(name, school, round_joined=self.current_round)
        self.players.append(new_player)
        self.player_name_entry.delete(0, "end")
        self.update_player_list_frame()
        self.unsaved_changes = True
        self.update_tournament_button_states()

    def update_player_list_frame(self):
        # Refreshes the scrollable frame displaying the list of players.
        for widget in self.player_scroll_frame.winfo_children():
            widget.destroy()
        self.selected_player = None
        self.selected_button = None
        sorted_players = sorted(self.players, key=lambda p: (p.school, p.name))
        for player in sorted_players:
            status = "ACTIVE" if player.is_active else "INACTIVE"
            display_text = f"{player.name} ({player.school})\nScore: {player.score} | Absences: {player.absent_count} | Status: {status}"
            btn = ctk.CTkButton(self.player_scroll_frame, text=display_text, anchor="w")
            # Pass the button itself to the command to allow selection highlighting
            btn.configure(command=lambda p=player, b=btn: self.select_player(p, b))
            btn.pack(pady=2, padx=5, fill="x")

    def select_player(self, player, button):
        # Highlights the selected player's button and stores the player object.
        if self.selected_button and self.selected_button.winfo_exists():
            self.selected_button.configure(fg_color=ctk.ThemeManager.theme["CTkButton"]["fg_color"])
        self.selected_player = player
        self.selected_button = button
        self.selected_button.configure(fg_color=ctk.ThemeManager.theme["CTkButton"]["hover_color"])

    def get_selected_player(self):
        # Returns the currently selected player or shows an error if none is selected.
        if self.selected_player:
            return self.selected_player
        messagebox.showerror("Error", "Please select a player from the list first.")
        return None

    def set_player_status_inactive(self):
        # Sets the selected player's status to inactive.
        player = self.get_selected_player()
        if player:
            player.is_active = False
            self.update_player_list_frame()
            # Pairings exist for current round
            if self.result_widgets:
                messagebox.showinfo("Player Status Updated",
                                    f"'{player.name}' has been marked as INACTIVE. This change will apply to future pairings. For the current round, please manually mark them 'Absent' if needed.")
            else:
                messagebox.showinfo("Player Status Updated", f"'{player.name}' has been marked as INACTIVE.")
            self.unsaved_changes = True

    def set_player_status_active(self):
        # Sets the selected player's status to active.
        player = self.get_selected_player()
        if player:
            player.is_active = True
            self.update_player_list_frame()
            # Pairings exist for current round
            if self.result_widgets:
                messagebox.showinfo("Player Status Updated",
                                    f"'{player.name}' has been marked as ACTIVE. This change will apply to future pairings. Their status for the current round's pairings (if any) remains as it was when pairings were generated.")
            else:
                messagebox.showinfo("Player Status Updated", f"'{player.name}' has been marked as ACTIVE.")
            self.unsaved_changes = True

    def delete_player(self):
        # Deletes the selected player after confirmation.
        if self.result_widgets:
            messagebox.showerror("Error", "Cannot delete player while there are pending pairings/results. Please submit the current round first.")
            return
        player = self.get_selected_player()
        if player:
            if messagebox.askyesno("Confirm Deletion", f"Are you sure you want to permanently delete '{player.name}'?"):
                self.players.remove(player)
                self.update_player_list_frame()
                messagebox.showinfo("Success", f"'{player.name}' has been deleted.")
                self.unsaved_changes = True
                self.update_tournament_button_states()

    def import_data(self):
        # Loads tournament data from a JSON file.
        filepath = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        if not filepath: return
        try:
            with open(filepath, 'r') as f: data = json.load(f)
            self.players = [Player.from_dict(p_data) for p_data in data['players']]
            self.current_round = data['current_round']
            self.pairings_data = data.get('pairings_data', {})
            self.filename = filepath
            self.update_player_list_frame()
            self.round_label.configure(text=f"Current Round: {self.current_round}")
            self.rebuild_ui_from_saved_state()
            messagebox.showinfo("Success", f"Tournament loaded from {os.path.basename(filepath)}")
            self.unsaved_changes = False # State now matches the saved file
            self.update_tournament_button_states()
        except Exception as e:
            messagebox.showerror("Import Error", f"Failed to load file.\nError: {e}")

    def export_data(self):
        # Saves current tournament data to a JSON file.
        if not self.players:
            messagebox.showwarning("Export Warning", "There are no players to export.")
            return False
        filepath = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")],
                                                initialfile=f"tournament_round_{self.current_round}.json")
        if not filepath: return False
        data = {
            'current_round': self.current_round,
            'players': [p.to_dict() for p in self.players],
            'pairings_data': self.pairings_data
        }
        try:
            with open(filepath, 'w') as f: json.dump(data, f, indent=4)
            self.filename = filepath
            messagebox.showinfo("Success", f"Tournament state saved to {os.path.basename(filepath)}")
            self.unsaved_changes = False # Changes are now saved
            return True
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to save file.\nError: {e}")
            return False

    def _clear_and_rebuild_tournament_ui(self):
        # Clears the tournament display area and rebuilds it.
        for widget in self.tourney_display_container.winfo_children():
            widget.destroy()
        self.result_widgets = {}
        self._build_tournament_display()

    def generate_pairings_for_round(self):
        # Generates pairings for the current round based on player scores and history.
        if not self.players:
            messagebox.showerror("Error", "Cannot generate pairings without any players.")
            return
        if self.pairings_data:
            response = messagebox.askyesno("Confirm Regeneration",
                                             "Pairings for the current round already exist. Generating new pairings will discard the old ones. Continue?")
            if not response:
                return

        self._clear_and_rebuild_tournament_ui()
        self.pairings_data = {} # Clear previous round's pairings data

        ms_players = [p for p in self.players if p.school == "Middle School"]
        hs_players = [p for p in self.players if p.school == "High School"]

        # Pairing and color assignment are distinct steps
        ms_raw_pairings, ms_bye, ms_active_in_bracket = self._run_pairing_algorithm(ms_players)
        hs_raw_pairings, hs_bye, hs_active_in_bracket = self._run_pairing_algorithm(hs_players)

        ms_colored_pairings = self._assign_colors_to_pairings(ms_raw_pairings)
        hs_colored_pairings = self._assign_colors_to_pairings(hs_raw_pairings)

        # Save the colored pairings (by player name) for persistence
        self.pairings_data['Middle School'] = {
            'pairings': [(w.name, b.name) for w, b in ms_colored_pairings],
            'bye': ms_bye.name if ms_bye else None,
            'active': [p.name for p in ms_active_in_bracket]
        }
        self.pairings_data['High School'] = {
            'pairings': [(w.name, b.name) for w, b in hs_colored_pairings],
            'bye': hs_bye.name if hs_bye else None,
            'active': [p.name for p in hs_active_in_bracket]
        }

        self._display_and_create_results_ui("Middle School", ms_colored_pairings, ms_bye, self.ms_results_textbox, self.ms_results_frame)
        self._display_and_create_results_ui("High School", hs_colored_pairings, hs_bye, self.hs_results_textbox, self.hs_results_frame)
        self.unsaved_changes = True
        self.update_tournament_button_states()

    def rebuild_ui_from_saved_state(self):
        # Rebuilds the tournament UI based on loaded pairings data.
        if not self.pairings_data:
            self.update_tournament_button_states()
            return
        self._clear_and_rebuild_tournament_ui()
        player_map = {p.name: p for p in self.players}
        for bracket in ["Middle School", "High School"]:
            if bracket in self.pairings_data and self.pairings_data[bracket]:
                data = self.pairings_data[bracket]
                # Reconstruct colored pairings from saved data using player objects
                colored_pairings = []
                for w_name, b_name in data['pairings']:
                    white_player = player_map.get(w_name)
                    black_player = player_map.get(b_name)
                    if white_player and black_player:
                        colored_pairings.append((white_player, black_player))
                    else:
                        print(f"Warning: Player not found during UI rebuild for pairing {w_name} vs {b_name}")

                bye_player = player_map.get(data['bye']) if data['bye'] else None
                textbox = self.ms_results_textbox if bracket == "Middle School" else self.hs_results_textbox
                scroll_frame = self.ms_results_frame if bracket == "Middle School" else self.hs_results_frame
                self._display_and_create_results_ui(bracket, colored_pairings, bye_player, textbox, scroll_frame)
        self.update_tournament_button_states()

    def _assign_colors_to_pairings(self, pairings):
        # Assigns colors (White/Black) to players in each pairing based on color history.
        colored_pairings = []
        for p1, p2 in pairings:
            p1_whites = p1.color_history.count('W')
            p1_blacks = p1.color_history.count('B')
            p2_whites = p2.color_history.count('W')
            p2_blacks = p2.color_history.count('B')

            # Player with more past White games (stronger pull to Black) gets Black
            if (p1_whites - p1_blacks) > (p2_whites - p2_blacks):
                white_player, black_player = p2, p1
            elif (p2_whites - p2_blacks) > (p1_whites - p1_blacks):
                white_player, black_player = p1, p2
            else:
                # If equal color balance, randomize
                white_player, black_player = random.sample([p1, p2], 2)
            colored_pairings.append((white_player, black_player))
        return colored_pairings

    def _display_and_create_results_ui(self, bracket_name, colored_pairings, bye_player, textbox, scroll_frame):
        # Displays standings and pairings, and creates UI widgets for result entry.
        textbox.configure(state="normal")
        textbox.delete("1.0", "end")

        # Display Standings
        standings_text = f"--- {bracket_name} Standings (Before Round {self.current_round}) ---\n"
        # Only include players who joined by the current round for standings display
        bracket_players = sorted([p for p in self.players if p.school == bracket_name and p.round_joined <= self.current_round],
                                 key=lambda p: p.score, reverse=True)
        for p in bracket_players:
            status = " (Inactive)" if not p.is_active else ""
            standings_text += f"{p.name:<25} {p.score:>5.1f} pts{status}\n"
        textbox.insert("end", standings_text + "\n")

        # Display Pairings
        pairings_text = f"--- {bracket_name} Pairings for Round {self.current_round} ---\n"
        pairings_text += f"{'Board':<7} {'White':<25} {'Black':<25}\n"
        pairings_text += "-" * 60 + "\n"

        self.result_widgets[bracket_name] = []

        for i, (white_player, black_player) in enumerate(colored_pairings):
            pairings_text += f"{i+1:<7} {white_player.name:<25} {black_player.name:<25}\n"

        if bye_player: pairings_text += f"\nBYE: {bye_player.name}\n"

        inactive_players_in_bracket = [p for p in bracket_players if not p.is_active]
        if inactive_players_in_bracket:
            pairings_text += "\n--- Inactive Players (Auto Absent Bye) ---\n"
            for p in inactive_players_in_bracket: pairings_text += f"- {p.name}\n"

        textbox.insert("end", pairings_text)
        textbox.configure(state="disabled")

        # Clear previous result input widgets
        for widget in scroll_frame.winfo_children():
            widget.destroy()

        # Create result input widgets for each pairing
        for i, (white_player, black_player) in enumerate(colored_pairings):
            pair_frame = ctk.CTkFrame(scroll_frame)
            pair_frame.pack(fill="x", padx=5, pady=4)
            result_var = tk.StringVar(value="TBD")
            absent_p1_var = tk.BooleanVar(); absent_p2_var = tk.BooleanVar()

            # Pre-check absent if player is inactive
            if not white_player.is_active:
                absent_p1_var.set(True)
            if not black_player.is_active:
                absent_p2_var.set(True)

            ctk.CTkLabel(pair_frame, text=f"B{i+1}:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(5, 10))
            w_win = ctk.CTkRadioButton(pair_frame, text=f"{white_player.name} (W)", variable=result_var, value=f"{white_player.name}_win")
            w_absent = ctk.CTkCheckBox(pair_frame, text="Absent", variable=absent_p1_var, width=1)
            draw_btn = ctk.CTkRadioButton(pair_frame, text="Draw", variable=result_var, value="draw")
            b_win = ctk.CTkRadioButton(pair_frame, text=f"{black_player.name} (B)", variable=result_var, value=f"{black_player.name}_win")
            b_absent = ctk.CTkCheckBox(pair_frame, text="Absent", variable=absent_p2_var, width=1)

            w_win.pack(side="left", padx=5, expand=True, fill='x'); w_absent.pack(side="left", padx=(0,15)); draw_btn.pack(side="left", padx=5)
            b_win.pack(side="left", padx=15, expand=True, fill='x'); b_absent.pack(side="left", padx=(0,5))

            widget_dict = {
                'white': white_player,
                'black': black_player,
                'result_var': result_var,
                'absent_white_var': absent_p1_var,
                'absent_black_var': absent_p2_var,
                'widgets': {'w_win': w_win, 'draw': draw_btn, 'b_win': b_win}
            }
            # Configure commands for checkboxes to handle disabling radio buttons
            w_absent.configure(command=lambda d=widget_dict: self._on_absence_toggle(d))
            b_absent.configure(command=lambda d=widget_dict: self._on_absence_toggle(d))

            # Apply initial state for inactive players
            if not white_player.is_active:
                w_absent.select()
                self._on_absence_toggle(widget_dict)
            if not black_player.is_active:
                b_absent.select()
                self._on_absence_toggle(widget_dict)

            self.result_widgets[bracket_name].append(widget_dict)

    def _run_pairing_algorithm(self, players_in_bracket):
        # Implements the Swiss-style pairing algorithm for a given bracket.
        # Filter for active players who joined by the current round
        initial_active_players = [p for p in players_in_bracket if p.is_active and p.round_joined <= self.current_round]

        if len(initial_active_players) < 2:
            return [], initial_active_players[0] if initial_active_players else None, initial_active_players

        players_pool_for_pairing = list(initial_active_players)

        # Step 1: Determine Bye Player (if odd number of players)
        bye_player = None
        # Prioritize players who haven't had a bye, then lowest score, then alphabetically
        players_for_bye_consideration = sorted(players_pool_for_pairing, key=lambda p: (p.had_pairing_bye, p.score, p.name))

        if len(players_for_bye_consideration) % 2 != 0:
            for p in players_for_bye_consideration:
                if not p.had_pairing_bye:
                    bye_player = p
                    break
            if not bye_player: # If everyone has had a bye, pick the one with the lowest score
                bye_player = players_for_bye_consideration[0]

            players_pool_for_pairing.remove(bye_player)

        # Step 2: Sort remaining active players by score (descending)
        players_to_pair = sorted(players_pool_for_pairing, key=lambda p: p.score, reverse=True)

        pairings = []
        unpaired_pool = set(players_to_pair)

        while len(unpaired_pool) >= 2:
            # Select the highest-scoring unpaired player (or random from highest score group)
            max_score = max(p.score for p in unpaired_pool)
            highest_score_players = [p for p in unpaired_pool if p.score == max_score]
            p1 = random.choice(highest_score_players)

            unpaired_pool.remove(p1)

            best_p2 = None
            # Criteria for best opponent: (played_before, score_diff, num_times_played) - lower is better
            best_criteria = (True, float('inf'), float('inf'))

            candidates = list(unpaired_pool)
            random.shuffle(candidates) # Randomize candidates to break ties naturally

            for p2 in candidates:
                played_before = p2.name in p1.opponent_history
                score_diff = abs(p1.score - p2.score)
                num_times_played = p1.opponent_history.count(p2.name) if played_before else 0

                current_criteria = (played_before, score_diff, num_times_played)

                if current_criteria < best_criteria:
                    best_criteria = current_criteria
                    best_p2 = p2

            if best_p2:
                pairings.append((p1, best_p2))
                unpaired_pool.remove(best_p2)
            else:
                unpaired_pool.add(p1) # Add p1 back if no match found (WON'T HAPPEN THOUGH, I think)
                break

        return pairings, bye_player, initial_active_players

    def _on_absence_toggle(self, result_data):
        # Handles the logic when an 'Absent' checkbox is toggled, disabling/enabling result radio buttons.
        is_white_absent = result_data['absent_white_var'].get()
        is_black_absent = result_data['absent_black_var'].get()

        for widget in result_data['widgets'].values():
            if is_white_absent or is_black_absent:
                widget.configure(state="disabled")
            else:
                widget.configure(state="normal")

        if is_white_absent or is_black_absent:
            result_data['result_var'].set("TBD") # Reset result if someone is marked absent

    def submit_results(self):
        # Processes and applies the results entered for the current round, updates player scores and histories.
        if not self.result_widgets:
            messagebox.showerror("Error", "No pairings have been generated for this round.")
            return

        # Validate that all results have been entered (unless players are marked absent)
        for bracket_name, results in self.result_widgets.items():
            for i, res_data in enumerate(results):
                absent_white = res_data['absent_white_var'].get()
                absent_black = res_data['absent_black_var'].get()
                result_pending = res_data['result_var'].get() == "TBD"

                if not (absent_white or absent_black) and result_pending:
                    messagebox.showerror("Missing Result",
                                         f"Please enter a result for Board {i+1} in the {bracket_name} bracket, or mark a player as absent.")
                    return

        # Reset had_pairing_bye for all players for the next round's calculation
        for p in self.players:
            p.had_pairing_bye = False

        # Process results for paired players
        for bracket_name, results in self.result_widgets.items():
            for res_data in results:
                white_p, black_p = res_data['white'], res_data['black']
                absent_white = res_data['absent_white_var'].get()
                absent_black = res_data['absent_black_var'].get()

                # Handle cases where one or both players are absent
                if absent_white or absent_black:
                    if absent_white:
                        if white_p.absent_count < 3: white_p.score += 0.5
                        white_p.absent_count += 1
                        white_p.opponent_history.append("Absent" if white_p.is_active else "Inactive Bye")
                        white_p.color_history.append("N/A")
                    if absent_black:
                        if black_p.absent_count < 3: black_p.score += 0.5
                        black_p.absent_count += 1
                        black_p.opponent_history.append("Absent" if black_p.is_active else "Inactive Bye")
                        black_p.color_history.append("N/A")

                    # Award full point to the present player if opponent is absent
                    if absent_white and not absent_black:
                        black_p.score += 1.0
                        black_p.opponent_history.append(f"{white_p.name} (Forfeit)")
                        black_p.color_history.append("N/A")
                    elif absent_black and not absent_white:
                        white_p.score += 1.0
                        white_p.opponent_history.append(f"{black_p.name} (Forfeit)")
                        white_p.color_history.append("N/A")
                    continue

                # If both players were present, process the game result
                result = res_data['result_var'].get()
                if result == f"{white_p.name}_win":
                    white_p.score += 1.0
                elif result == f"{black_p.name}_win":
                    black_p.score += 1.0
                elif result == "draw":
                    white_p.score += 0.5
                    black_p.score += 0.5

                # Update opponent and color history for present players
                white_p.opponent_history.append(black_p.name)
                white_p.color_history.append('W')
                black_p.opponent_history.append(white_p.name)
                black_p.color_history.append('B')

        # Handle assigned pairing byes
        for bracket, data in self.pairings_data.items():
            bye_name = data.get('bye')
            if bye_name:
                bye_p = next((p for p in self.players if p.name == bye_name), None)
                if bye_p and bye_p.is_active: # Only active players get points for pairing bye
                    bye_p.score += 1.0
                    bye_p.had_pairing_bye = True
                    bye_p.opponent_history.append("Pairing Bye")
                    bye_p.color_history.append("N/A")

        # Handle inactive players who were not part of any pairing
        all_paired_players_in_round = set()
        for b_data in self.result_widgets.values():
            for r_data in b_data:
                all_paired_players_in_round.add(r_data['white'])
                all_paired_players_in_round.add(r_data['black'])

        for bracket_data in self.pairings_data.values():
            bye_name = bracket_data.get('bye')
            if bye_name:
                bye_p = next((p for p in self.players if p.name == bye_name), None)
                if bye_p and bye_p.is_active:
                    all_paired_players_in_round.add(bye_p)

        for p in self.players:
            # If a player is inactive and wasn't explicitly part of a pairing or a pairing bye
            if not p.is_active and p not in all_paired_players_in_round:
                if p.absent_count < 3: p.score += 0.5
                p.absent_count += 1
                p.opponent_history.append("Inactive Bye")
                p.color_history.append("N/A")

        self.current_round += 1
        self.round_label.configure(text=f"Current Round: {self.current_round}")
        self.pairings_data = {} # Clear pairings after results are submitted
        self._clear_and_rebuild_tournament_ui()
        self.update_player_list_frame()
        messagebox.showinfo("Success", f"Round {self.current_round - 1} finalized. Ready for Round {self.current_round}.")
        self.unsaved_changes = True
        self.update_tournament_button_states()

    def update_tournament_button_states(self):
        # Updates the enabled/disabled state of tournament control buttons based on current state.
        # Check if there are enough active players to generate pairings in any bracket
        has_enough_active_players = False
        ms_active = [p for p in self.players if p.school == "Middle School" and p.is_active and p.round_joined <= self.current_round]
        hs_active = [p for p in self.players if p.school == "High School" and p.is_active and p.round_joined <= self.current_round]
        if len(ms_active) >= 2 or len(hs_active) >= 2:
            has_enough_active_players = True

        # If pairings are currently displayed, enable both buttons
        if self.result_widgets and any(self.result_widgets.values()):
            self.generate_pairings_button.configure(state="normal")
            self.submit_results_button.configure(state="normal")
        else: # No pairings currently displayed
            self.generate_pairings_button.configure(state="normal" if has_enough_active_players else "disabled")
            self.submit_results_button.configure(state="disabled")

    def on_closing(self):
        # Handles the application closing event, prompting to save unsaved changes.
        if self.unsaved_changes:
            response = messagebox.askyesnocancel("Quit",
                                                 "You have unsaved changes. Do you want to save before quitting?")
            if response is True: # Yes, save
                if self.export_data(): # If save was successful
                    self.destroy()
            elif response is False: # No, don't save
                self.destroy()
            # If response is None (Cancel), do nothing
        else:
            self.destroy()

if __name__ == "__main__":
    app = TournamentApp()
    app.mainloop()
