import tkinter as tk
import customtkinter as ctk
from tkinter import filedialog, messagebox
import json
import random
import os

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# Represents a single player in the tournament.
class Player:
    def __init__(self, name, school, is_active=True, score=0.0, opponent_history=None, 
                 color_history=None, absent_count=0, had_pairing_bye=False, round_joined=1):
        self.name = name
        self.school = school
        self.is_active = is_active
        self.score = score
        # Initialize lists if they are None (important for mutable default arguments)
        self.opponent_history = opponent_history if opponent_history is not None else []
        self.color_history = color_history if color_history is not None else []
        self.absent_count = absent_count
        self.had_pairing_bye = had_pairing_bye
        self.round_joined = round_joined

    # Convert player object's attributes into a dictionary for JSON
    def to_dict(self):
        return self.__dict__

    # Creates player object from a dictionary
    @classmethod
    def from_dict(cls, data):
        return cls(**data)

    def __repr__(self): # for debugging
        return f"Player({self.name}, {self.school}, Score: {self.score})"

# The main application class for the Tournament Manager GUI.
class TournamentApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Chess Club Tournament Manager")
        self.geometry("1200x850")

        self.players = []
        self.current_round = 1
        self.filename = None # stores the path of the current saved file (if any)
        self.pairings_data = {}
        
        # Flag for unsaved changes
        self.unsaved_changes = False

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.tabview = ctk.CTkTabview(self, width=250)
        self.tabview.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        # Tabs
        self.tabview.add("Player Management")
        self.tabview.add("Tournament")
        self.tabview.add("Help & Rules")

        # Call methods
        self.create_player_management_tab()
        self.create_tournament_tab()
        self.create_help_tab()

        # UI state
        self.result_widgets = {}
        self.selected_player = None
        self.selected_button = None
        
        # Bug fix: intercept the window close event.
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    # Sets up the 'Player Management' tab with widgets for adding, managing, and importing/exporting player data.
    def create_player_management_tab(self):
        pm_tab = self.tabview.tab("Player Management")
        pm_tab.grid_columnconfigure(1, weight=1)
        pm_tab.grid_rowconfigure(0, weight=1)

        left_frame = ctk.CTkFrame(pm_tab, width=280)
        left_frame.grid(row=0, column=0, padx=(0, 20), sticky="ns")
        left_frame.grid_propagate(False)

        # Frame for adding new players
        add_player_frame = ctk.CTkFrame(left_frame)
        add_player_frame.pack(pady=20, padx=20, fill="x")
        ctk.CTkLabel(add_player_frame, text="Add New Player", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(0,10))
        self.player_name_entry = ctk.CTkEntry(add_player_frame, placeholder_text="Player Name")
        self.player_name_entry.pack(pady=5, fill="x")
        self.school_var = tk.StringVar(value="Middle School")
        
        # Radio buttons for selecting school type
        ctk.CTkRadioButton(add_player_frame, text="Middle School", variable=self.school_var, value="Middle School").pack(anchor="w", padx=10, pady=2)
        ctk.CTkRadioButton(add_player_frame, text="High School", variable=self.school_var, value="High School").pack(anchor="w", padx=10, pady=2)
        ctk.CTkButton(add_player_frame, text="Add Player", command=self.add_player).pack(pady=10, fill="x")

        # Frame for managing selected players (inactive/active/delete)
        manage_frame = ctk.CTkFrame(left_frame)
        manage_frame.pack(pady=20, padx=20, fill="x")
        ctk.CTkLabel(manage_frame, text="Manage Selected Player", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(0,10))
        ctk.CTkButton(manage_frame, text="Set as INACTIVE", command=self.set_player_status_inactive).pack(pady=5, fill="x")
        ctk.CTkButton(manage_frame, text="Set as ACTIVE", command=self.set_player_status_active).pack(pady=5, fill="x")
        ctk.CTkButton(manage_frame, text="Delete Player", fg_color="#D32F2F", hover_color="#B71C1C", command=self.delete_player).pack(pady=5, fill="x")

        # Frame for file operations (import/export)
        file_frame = ctk.CTkFrame(left_frame)
        file_frame.pack(pady=20, padx=20, fill="x")
        ctk.CTkLabel(file_frame, text="File Operations", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(0,10))
        ctk.CTkButton(file_frame, text="Import Tournament (.json)", command=self.import_data).pack(pady=5, fill="x")
        ctk.CTkButton(file_frame, text="Export Tournament (.json)", command=self.export_data).pack(pady=5, fill="x")

        # Frame for displaying the list of current players (right side of the tab)
        player_list_frame = ctk.CTkFrame(pm_tab)
        player_list_frame.grid(row=0, column=1, sticky="nsew")
        ctk.CTkLabel(player_list_frame, text="Current Player Roster", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        # Scrollable frame to hold player buttons
        self.player_scroll_frame = ctk.CTkScrollableFrame(player_list_frame)
        self.player_scroll_frame.pack(expand=True, fill="both", padx=10, pady=10)

    # Sets up the 'Tournament' tab with controls for generating pairings, submitting results, and displaying match information.
    def create_tournament_tab(self):
        self.tourney_tab = self.tabview.tab("Tournament")
        self.tourney_tab.grid_columnconfigure(0, weight=1)
        self.tourney_tab.grid_rowconfigure(1, weight=1)

        # Control frame at the top of the tournament tab
        control_frame = ctk.CTkFrame(self.tourney_tab)
        control_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
       
        # Label to display the current round number
        self.round_label = ctk.CTkLabel(control_frame, text=f"Current Round: {self.current_round}", font=ctk.CTkFont(size=16, weight="bold"))
        self.round_label.pack(side="left", padx=20)
        
        # Buttons to submit results or generate new pairings
        ctk.CTkButton(control_frame, text="Submit Results & Finalize Round", command=self.submit_results).pack(side="right", padx=10)
        ctk.CTkButton(control_frame, text="Generate Pairings for Next Round", command=self.generate_pairings_for_round).pack(side="right", padx=10)
        
        # Container frame for displaying tournament information (pairings, results input)
        self.tourney_display_container = ctk.CTkFrame(self.tourney_tab, fg_color="transparent")
        self.tourney_display_container.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.tourney_display_container.grid_columnconfigure(0, weight=1)
        self.tourney_display_container.grid_columnconfigure(1, weight=1)
        self.tourney_display_container.grid_rowconfigure(0, weight=1)
        self._build_tournament_display() # build the actual display elements within this container

    # Creates the UI elements for displaying pairings and entering results for both Middle School and High School brackets.
    # This method is called initially and whenever the tournament UI needs to be rebuilt.
    def _build_tournament_display(self):
        # Middle School bracket display container
        ms_container = ctk.CTkFrame(self.tourney_display_container)
        ms_container.grid(row=0, column=0, padx=(0, 5), pady=0, sticky="nsew")
        # Configure grid for MS container: 3 rows (label, textbox, scrollable frame)
        ms_container.grid_rowconfigure(1, weight=1); ms_container.grid_rowconfigure(2, weight=2)
        ms_container.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(ms_container, text="Middle School Bracket", font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, pady=5)
        # Textbox to display standings and pairings
        self.ms_results_textbox = ctk.CTkTextbox(ms_container, wrap="word", font=("Courier New", 12))
        self.ms_results_textbox.grid(row=1, column=0, sticky="nsew", padx=5, pady=(0,5))
        self.ms_results_textbox.configure(state="disabled")
        # Scrollable frame where result input widgets will be placed
        self.ms_results_frame = ctk.CTkScrollableFrame(ms_container, label_text="Enter Results")
        self.ms_results_frame.grid(row=2, column=0, sticky="nsew", padx=5, pady=(5,5))

        # Same structure for High School bracket
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

    # Sets up the Help & Rules tab with a read-only text box with instructions and tournament rules.
    def create_help_tab(self):
        help_tab = self.tabview.tab("Help & Rules")
        help_tab.grid_columnconfigure(0, weight=1)
        help_tab.grid_rowconfigure(0, weight=1)
        help_textbox = ctk.CTkTextbox(help_tab, wrap="word", font=("Segoe UI", 13))
        help_textbox.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        help_content = """
        --- HOW TO USE THE PROGRAM ---

        1.  Player Management Tab:
            - Add Players: Enter a player's name, select their school (Middle/High), and click "Add Player". New players can be added at any time.
            - Manage Players: Select a player from the list on the right. You can then mark them as "Inactive" (if they leave the club) or "Active". Inactive players will automatically receive absent byes.
            - Import/Export: Use the buttons to save your current tournament progress to a .json file or load a previous tournament. ALWAYS export your progress when you are done.

        2.  Tournament Tab:
            - Generate Pairings: Once players are added, click "Generate Pairings for Next Round". This will use the pairing logic to create matches for both brackets.
            - View Pairings & Enter Results: The pairings will appear in the text boxes. You can copy this text to a Google Doc. Below the pairings, controls will appear to enter results.
            - Mark Absences: For players who did not show up, check the "Absent" box next to their name.
            - Submit Results: After setting all results (Win/Loss/Draw) and marking any absences, click "Submit Results & Finalize Round". This will calculate scores, update player histories, and prepare for the next round.

        --- PAIRING LOGIC PRIORITY ---

        The program uses a Swiss-style pairing system with the following priorities:

        1.  No Duplicate Opponents: A player will NEVER be paired against someone they have already played. This is the highest priority.
        2.  Score Matching: Players are paired against others in the same score group. The system works down from the top score.
        3.  Color Balancing: The system tries to give players the color they have played less. If they have played an equal number of games as White and Black, it will try to alternate from their last game.
        4.  Randomness: If multiple opponents are equally valid after the above rules, one is chosen randomly.

        --- SCORING AND RULES ---

        -   Win: 1.0 point
        -   Draw: 0.5 points
        -   Loss: 0.0 points
        -   Pairing Bye: 1.0 point. This happens when there is an odd number of players. A player cannot receive a pairing bye two rounds in a row.
        -   Absent Bye: 0.5 points. This is awarded when a player is marked "Absent". A player will only receive points for their first THREE absences. After that, absences are worth 0 points.
        -   Inactive Players: Automatically receive absent byes each round.
        """
        help_textbox.insert("1.0", help_content)
        help_textbox.configure(state="disabled")

    # Adds new player to the tournament roster based on input fields
    # Checks if name not empty, name not duplicate, etc
    def add_player(self):
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
        self.unsaved_changes = True # the flag bug fix, there will be more of these tho

    # Changes the scrollable frame that shows the list of players
    def update_player_list_frame(self):
        for widget in self.player_scroll_frame.winfo_children():
            widget.destroy()
        self.selected_player = None
        self.selected_button = None
        # Sort players for consistent display (by school, then by name)
        sorted_players = sorted(self.players, key=lambda p: (p.school, p.name))
        for player in sorted_players:
            status = "ACTIVE" if player.is_active else "INACTIVE"
            display_text = f"{player.name} ({player.school})\nScore: {player.score} | Absences: {player.absent_count} | Status: {status}"
             # Create a button for each player
            btn = ctk.CTkButton(self.player_scroll_frame, text=display_text, anchor="w",
                                command=lambda p=player, b=None: self.select_player(p, b))
            # A bit of a hack to pass the button to its own command
            # Stops issue with variable scope
            btn.configure(command=lambda p=player, b=btn: self.select_player(p, b))
            btn.pack(pady=2, padx=5, fill="x")

    # Highlights and stores selected player's button and object respectively
    def select_player(self, player, button):
        if self.selected_button and self.selected_button.winfo_exists():
            self.selected_button.configure(fg_color=ctk.ThemeManager.theme["CTkButton"]["fg_color"])
        self.selected_player = player
        self.selected_button = button
        self.selected_button.configure(fg_color=ctk.ThemeManager.theme["CTkButton"]["hover_color"])

    # Sets selected player
    def get_selected_player(self):
        if self.selected_player:
            return self.selected_player
        messagebox.showerror("Error", "Please select a player from the list first.")
        return None

    # Sets selected player's status to inactive
    def set_player_status_inactive(self):
        player = self.get_selected_player()
        if player:
            player.is_active = False
            self.update_player_list_frame()
            messagebox.showinfo("Success", f"'{player.name}' has been marked as INACTIVE.")
            self.unsaved_changes = True

    # Sets selected player's status to active
    def set_player_status_active(self):
        player = self.get_selected_player()
        if player:
            player.is_active = True
            self.update_player_list_frame()
            messagebox.showinfo("Success", f"'{player.name}' has been marked as ACTIVE.")
            self.unsaved_changes = True
    
    # Deletes player after confirmation
    def delete_player(self):
        player = self.get_selected_player()
        if player:
            if messagebox.askyesno("Confirm Deletion", f"Are you sure you want to permanently delete '{player.name}'?"):
                self.players.remove(player)
                self.update_player_list_frame()
                messagebox.showinfo("Success", f"'{player.name}' has been deleted.")
                self.unsaved_changes = True

    def import_data(self):
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
            self.unsaved_changes = False # Bug fix: state now matches the saved file
        except Exception as e:
            messagebox.showerror("Import Error", f"Failed to load file.\nError: {e}")

    def export_data(self):
        if not self.players:
            messagebox.showwarning("Export Warning", "There are no players to export.")
            return False # Bug fix: return status
        filepath = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")],
                                                initialfile=f"tournament_round_{self.current_round}.json")
        if not filepath: return False # Bug fix: return status
        data = {
            'current_round': self.current_round,
            'players': [p.to_dict() for p in self.players],
            'pairings_data': self.pairings_data
        }
        try:
            with open(filepath, 'w') as f: json.dump(data, f, indent=4)
            self.filename = filepath
            messagebox.showinfo("Success", f"Tournament state saved to {os.path.basename(filepath)}")
            self.unsaved_changes = False # Bug fix: Changes are now saved
            return True # Bug fix: Return status
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to save file.\nError: {e}")
            return False # Bug fix: Return status

    def _clear_and_rebuild_tournament_ui(self):
        for widget in self.tourney_display_container.winfo_children():
            widget.destroy()
        self.result_widgets = {}
        # Do not clear pairings_data here, it might be needed for saving
        self._build_tournament_display()

    def generate_pairings_for_round(self):
        if not self.players:
            messagebox.showerror("Error", "Cannot generate pairings without any players.")
            return
        
        self._clear_and_rebuild_tournament_ui()
        self.pairings_data = {} # Clear previous round's pairings data

        ms_players = [p for p in self.players if p.school == "Middle School"]
        hs_players = [p for p in self.players if p.school == "High School"]
        
        # Pairing and color assignment must be distinct steps
        ms_raw_pairings, ms_bye = self._run_pairing_algorithm(ms_players)
        hs_raw_pairings, hs_bye = self._run_pairing_algorithm(hs_players)

        ms_colored_pairings = self._assign_colors_to_pairings(ms_raw_pairings)
        hs_colored_pairings = self._assign_colors_to_pairings(hs_raw_pairings)

        # Save the colored pairings (by name) to be persistent
        self.pairings_data['Middle School'] = {
            'pairings': [(w.name, b.name) for w, b in ms_colored_pairings], 
            'bye': ms_bye.name if ms_bye else None
        }
        self.pairings_data['High School'] = {
            'pairings': [(w.name, b.name) for w, b in hs_colored_pairings], 
            'bye': hs_bye.name if hs_bye else None
        }

        self._display_and_create_results_ui("Middle School", ms_colored_pairings, ms_bye, self.ms_results_textbox, self.ms_results_frame)
        self._display_and_create_results_ui("High School", hs_colored_pairings, hs_bye, self.hs_results_textbox, self.hs_results_frame)
        self.unsaved_changes = True

    def rebuild_ui_from_saved_state(self):
        if not self.pairings_data:
            return
        self._clear_and_rebuild_tournament_ui()
        player_map = {p.name: p for p in self.players}
        for bracket in ["Middle School", "High School"]:
            if bracket in self.pairings_data and self.pairings_data[bracket]:
                data = self.pairings_data[bracket]
                # Reconstruct colored pairings from saved data
                colored_pairings = [(player_map[w_name], player_map[b_name]) for w_name, b_name in data['pairings']]
                bye_player = player_map.get(data['bye']) if data['bye'] else None
                textbox = self.ms_results_textbox if bracket == "Middle School" else self.hs_results_textbox
                scroll_frame = self.ms_results_frame if bracket == "Middle School" else self.hs_results_frame
                self._display_and_create_results_ui(bracket, colored_pairings, bye_player, textbox, scroll_frame)

    # Color assignment logic
    def _assign_colors_to_pairings(self, pairings):
        colored_pairings = []
        for p1, p2 in pairings:
            p1_whites = p1.color_history.count('W')
            p1_blacks = p1.color_history.count('B')
            p2_whites = p2.color_history.count('W')
            p2_blacks = p2.color_history.count('B')
            
            # Player with a stronger "pull" to play Black (i.e., more past White games) gets Black
            if (p1_whites - p1_blacks) > (p2_whites - p2_blacks):
                white_player, black_player = p2, p1
            elif (p2_whites - p2_blacks) > (p1_whites - p1_blacks):
                white_player, black_player = p1, p2
            else:
                # If equal, randomize
                white_player, black_player = random.sample([p1, p2], 2)
            colored_pairings.append((white_player, black_player))
        return colored_pairings

    def _display_and_create_results_ui(self, bracket_name, colored_pairings, bye_player, textbox, scroll_frame):
        textbox.configure(state="normal")
        textbox.delete("1.0", "end")
        standings_text = f"--- {bracket_name} Standings (Before Round {self.current_round}) ---\n"
        bracket_players = sorted([p for p in self.players if p.school == bracket_name], key=lambda p: p.score, reverse=True)
        for p in bracket_players:
            status = " (Inactive)" if not p.is_active else ""
            standings_text += f"{p.name:<25} {p.score:>5.1f} pts{status}\n"
        textbox.insert("end", standings_text + "\n")
        
        pairings_text = f"--- {bracket_name} Pairings for Round {self.current_round} ---\n"
        pairings_text += f"{'Board':<7} {'White':<25} {'Black':<25}\n"
        pairings_text += "-" * 60 + "\n"
        
        self.result_widgets[bracket_name] = []
        
        # This loop now receives pre-colored pairings and just displays them
        for i, (white_player, black_player) in enumerate(colored_pairings):
            pairings_text += f"{i+1:<7} {white_player.name:<25} {black_player.name:<25}\n"
        
        if bye_player: pairings_text += f"\nBYE: {bye_player.name}\n"
        inactive_players = [p for p in bracket_players if not p.is_active]
        if inactive_players:
            pairings_text += "\n--- Inactive Players (Auto Absent Bye) ---\n"
            for p in inactive_players: pairings_text += f"- {p.name}\n"
        
        textbox.insert("end", pairings_text)
        textbox.configure(state="disabled")
        
        for i, (white_player, black_player) in enumerate(colored_pairings):
            pair_frame = ctk.CTkFrame(scroll_frame)
            pair_frame.pack(fill="x", padx=5, pady=4)
            result_var = tk.StringVar(value="TBD")
            absent_p1_var = tk.BooleanVar(); absent_p2_var = tk.BooleanVar()
            ctk.CTkLabel(pair_frame, text=f"B{i+1}:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(5, 10))
            w_win = ctk.CTkRadioButton(pair_frame, text=f"{white_player.name} (W)", variable=result_var, value=f"{white_player.name}_win")
            w_absent = ctk.CTkCheckBox(pair_frame, text="Absent", variable=absent_p1_var, width=1)
            draw_btn = ctk.CTkRadioButton(pair_frame, text="Draw", variable=result_var, value="draw")
            b_win = ctk.CTkRadioButton(pair_frame, text=f"{black_player.name} (B)", variable=result_var, value=f"{black_player.name}_win")
            b_absent = ctk.CTkCheckBox(pair_frame, text="Absent", variable=absent_p2_var, width=1)
            w_win.pack(side="left", padx=5, expand=True, fill='x'); w_absent.pack(side="left", padx=(0,15)); draw_btn.pack(side="left", padx=5)
            b_win.pack(side="left", padx=15, expand=True, fill='x'); b_absent.pack(side="left", padx=(0,5))
            widget_dict = {'white': white_player, 'black': black_player, 'result_var': result_var, 'absent_white_var': absent_p1_var, 'absent_black_var': absent_p2_var, 'widgets': {'w_win': w_win, 'draw': draw_btn, 'b_win': b_win}}
            w_absent.configure(command=lambda d=widget_dict: self._on_absence_toggle(d))
            b_absent.configure(command=lambda d=widget_dict: self._on_absence_toggle(d))
            self.result_widgets[bracket_name].append(widget_dict)

    def _run_pairing_algorithm(self, players_in_bracket):
        active_players = [p for p in players_in_bracket if p.is_active]
        if len(active_players) < 2:
            return [], active_players[0] if active_players else None
        random.shuffle(active_players)
        players_to_pair = sorted(active_players, key=lambda p: p.score, reverse=True)
        bye_player = None
        if len(players_to_pair) % 2 != 0:
            for i in range(len(players_to_pair) - 1, -1, -1):
                if not players_to_pair[i].had_pairing_bye:
                    bye_player = players_to_pair.pop(i)
                    break
            if not bye_player: bye_player = players_to_pair.pop()
        pairings, paired_indices = [], set()
        for i in range(len(players_to_pair)):
            if i in paired_indices: continue
            p1 = players_to_pair[i]
            for j in range(i + 1, len(players_to_pair)):
                if j in paired_indices: continue
                p2 = players_to_pair[j]
                if p2.name in p1.opponent_history: continue
                pairings.append((p1, p2))
                paired_indices.add(i)
                paired_indices.add(j) # Bug fix: was players_to_pair.index(p2), which is unsafe
                break
        return pairings, bye_player

    def _on_absence_toggle(self, result_data):
        is_white_absent = result_data['absent_white_var'].get()
        is_black_absent = result_data['absent_black_var'].get()
        if is_white_absent or is_black_absent:
            for widget in result_data['widgets'].values(): widget.configure(state="disabled")
            result_data['result_var'].set("TBD")
        else:
            for widget in result_data['widgets'].values(): widget.configure(state="normal")

    def submit_results(self):
        if not self.result_widgets:
            messagebox.showerror("Error", "No pairings have been generated for this round.")
            return

        # Validate that all results have been entered.
        for bracket_name, results in self.result_widgets.items():
            for i, res_data in enumerate(results):
                is_absent = res_data['absent_white_var'].get() or res_data['absent_black_var'].get()
                result_pending = res_data['result_var'].get() == "TBD"
                if not is_absent and result_pending:
                    messagebox.showerror("Missing Result", 
                                         f"Please enter a result for Board {i+1} in the {bracket_name} bracket, "
                                         "or mark a player as absent.")
                    return
        
        for p in self.players: p.had_pairing_bye = False
        
        for bracket_name, results in self.result_widgets.items():
            for res_data in results:
                white_p, black_p = res_data['white'], res_data['black']
                white_absent, black_absent = res_data['absent_white_var'].get(), res_data['absent_black_var'].get()
                
                if white_absent or black_absent:
                    if white_absent:
                        if white_p.absent_count < 3: white_p.score += 0.5
                        white_p.absent_count += 1; white_p.opponent_history.append("Absent"); white_p.color_history.append("N/A")
                    if black_absent:
                        if black_p.absent_count < 3: black_p.score += 0.5
                        black_p.absent_count += 1; black_p.opponent_history.append("Absent"); black_p.color_history.append("N/A")
                    
                    if white_absent and not black_absent:
                        black_p.score += 1.0; black_p.opponent_history.append(f"{white_p.name} (Forfeit)"); black_p.color_history.append("N/A")
                    if black_absent and not white_absent:
                        white_p.score += 1.0; white_p.opponent_history.append(f"{black_p.name} (Forfeit)"); white_p.color_history.append("N/A")
                    continue
                
                result = res_data['result_var'].get()
                if result == f"{white_p.name}_win": white_p.score += 1.0
                elif result == f"{black_p.name}_win": black_p.score += 1.0
                elif result == "draw": white_p.score += 0.5; black_p.score += 0.5
                
                white_p.opponent_history.append(black_p.name); white_p.color_history.append('W')
                black_p.opponent_history.append(white_p.name); black_p.color_history.append('B')
        
        all_paired_players = {p for b in self.result_widgets.values() for r in b for p in (r['white'], r['black'])}
        for p in self.players:
            if p not in all_paired_players and p.is_active:
                p.score += 1.0; p.had_pairing_bye = True; p.opponent_history.append("Pairing Bye"); p.color_history.append("N/A")
            elif not p.is_active:
                if p.absent_count < 3: p.score += 0.5
                p.absent_count += 1; p.opponent_history.append("Inactive Bye"); p.color_history.append("N/A")
        
        self.current_round += 1
        self.round_label.configure(text=f"Current Round: {self.current_round}")
        self.pairings_data = {} # Clear pairings after results are submitted
        self._clear_and_rebuild_tournament_ui()
        self.update_player_list_frame()
        messagebox.showinfo("Success", f"Round {self.current_round - 1} finalized. Ready for Round {self.current_round}.")
        self.unsaved_changes = True

    # New method to handle closing the application
    def on_closing(self):
        if self.unsaved_changes:
            response = messagebox.askyesnocancel("Quit", 
                                                 "You have unsaved changes. Do you want to save before quitting?")
            if response is True: # Yes
                if self.export_data(): # If save was successful
                    self.destroy()
                # else: user cancelled save dialog, so do nothing.
            elif response is False: # No
                self.destroy()
            # else (response is None): Cancel quit, do nothing.
        else:
            self.destroy()

if __name__ == "__main__":
    app = TournamentApp()
    app.mainloop()