import tkinter as tk
import tkinter.font as font
from tkinter import filedialog, messagebox, ttk
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg 
import os

class CSVEditorApp:
    def __init__(self, master):
        master.title("Outils de vérification des données")

        # ---------------- Change the fontsize ----------------
        self.default_font = font.nametofont("TkDefaultFont")
        self.default_font.configure(family="Arial", size=15)

        # ---------------- Top : options ----------------
        top = tk.Frame(master)
        top.pack(fill="x",side=tk.TOP, padx=10, pady=10)
        self.open_button = tk.Button(top, anchor="nw", text="Charger un fichier", command=self.select_file)
        self.open_button.pack(side="left",padx=5)

        # Save as CSV data
        self.save_button = tk.Button(top, anchor="n", text="Sauvegarder CSV", command=self.save_csv)
        self.save_button.pack(side="left", padx=5)

        # To save the figure
        self.savefig_button = tk.Button(top, anchor="n", text="Sauvegarder la figure",command=self.savefig)
        self.savefig_button.pack(side="left", padx=5)

        self.quit_button = tk.Button(top, anchor="ne", text="Quitter", command=master.quit)
        self.quit_button.pack(side="right",padx=5)

        # ---------------- Left panel: notebook ----------------
        left_panel = tk.Frame(master)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        self.notebook = ttk.Notebook(left_panel)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Did this in this order so that later i don't need to change the packing order
        self.tab3 = tk.Frame(self.notebook)
        self.notebook.add(self.tab3, text="Statistiques")

        self.tab1 = tk.Frame(self.notebook)
        self.notebook.add(self.tab1, text="Trous")
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_change)
        
        self.tab2 = tk.Frame(self.notebook)
        self.notebook.add(self.tab2, text="Outliers")
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_change)

        # ---------------- Widgets per tabs ----------------
        # --- Widgets TAB1 ---

        self.welcome_text = tk.Label(self.tab1, text="Charger un fichier pour lancer le traitement des trous.")
        self.welcome_text.pack(pady=10)

        self.question_label = tk.Label(self.tab1, text="", wraplength=320, justify="left")
        self.question_label.pack(fill="x",pady=8)

        self.answer_frame = tk.Frame(self.tab1)
        self.answer_frame.pack(pady=5)

        self.yes_button = tk.Button(self.answer_frame, text="Oui", command=lambda: self.handle_answer(True))
        self.no_button = tk.Button(self.answer_frame, text="Non", command=lambda: self.handle_answer(False))
    
        # --- Manual entry for isolated missing values ---
        self.manual_entry_label = tk.Label(self.tab1, text="ou entrer une valeur :")
        self.manual_entry = tk.Entry(self.tab1)
        self.manual_entry_button = tk.Button(self.tab1, text="Valider", command=self.handle_manual_value)
        self.hide_manual_entry() # Necessary to do like this because it is often called when using the first tab...

        # --- Widgets TAB2 ---

        # Titre champ début
        self.sup_label = tk.Label(self.tab2, text="Borne supérieure :")
        self.entry_sup = tk.Entry(self.tab2, width=15)
        self.entry_sup.bind("<Return>", self.preview_selection) # Preview of the data when the user presses "Enter"

        # Titre champ fin
        self.inf_label = tk.Label(self.tab2, text="Borne inférieure :")
        self.entry_inf = tk.Entry(self.tab2, width=15)
        self.entry_inf.bind("<Return>",self.preview_selection) # Preview of the data when the user presses "Enter"

        # Bouton pour supprimer la plage
        self.remove_range_button = tk.Button(
            self.tab2,
            text="Garder l'intervalle",
            command=self.remove_selected_range
        )

        # Button to start the outlier treatment
        self.welcome_text2 = tk.Label(self.tab2, text="Charger un fichier pour commencer le traitement des outliers.")
        self.welcome_text2.pack(pady=10)

        # bool to track visibility of tools for the second tab
        self.tab2_tools_visible = False

        # --- Widgets TAB3 ---

        # Statistical summary
        self.header_frame = tk.Frame(self.tab3)
        self.header_frame.pack(fill="x")

        self.sum_title = tk.Label(self.header_frame, text="Résumé statistique des données",font=("Arial",20))
        self.sum_title.pack(side="left", pady=10)

        # Refresh the statistics if the data have changed
        self.refresh_summary_button = tk.Button(self.header_frame, text="↻",command=self.update_stats)
        self.refresh_summary_button.pack(side="right",pady=10)

        # Text area for the statistics
        # Starting date
        self.sdate_frame = tk.Frame(self.tab3)
        self.sdate_frame.pack(fill="x")

        self.starting_date_label = tk.Label(self.sdate_frame, text="Date de début :")
        self.starting_date_label.pack(side="left",pady=5)
        self.starting_date_value = tk.Label(self.sdate_frame, text="Aucune donnée")
        self.starting_date_value.pack(side="right",pady=5)

        # Ending date
        self.edate_frame = tk.Frame(self.tab3)
        self.edate_frame.pack(fill="x")

        self.ending_date_label = tk.Label(self.edate_frame, text="Date de fin :")
        self.ending_date_label.pack(side="left",pady=5)
        self.ending_date_value = tk.Label(self.edate_frame, text="Aucune donnée")
        self.ending_date_value.pack(side="right",pady=5)

        # Timestep
        self.dt_frame = tk.Frame(self.tab3)
        self.dt_frame.pack(fill="x")

        self.dt_label = tk.Label(self.dt_frame, text="Pas de temps :")
        self.dt_label.pack(side="left",pady=5)
        self.dt_value = tk.Label(self.dt_frame, text="Aucune donnée")
        self.dt_value.pack(side="right",pady=5)

        # Mean
        self.mean_frame = tk.Frame(self.tab3)
        self.mean_frame.pack(fill="x")

        self.mean_label = tk.Label(self.mean_frame, text="Moyenne :")
        self.mean_label.pack(side="left",pady=5)
        self.mean_value = tk.Label(self.mean_frame, text="Aucune donnée")
        self.mean_value.pack(side="right",pady=5)

        # standard deviation
        self.std_frame = tk.Frame(self.tab3)
        self.std_frame.pack(fill="x")

        self.std_label = tk.Label(self.std_frame, text="Écart-type : ")
        self.std_label.pack(side="left",pady=5)
        self.std_value = tk.Label(self.std_frame, text="Aucune donnée")
        self.std_value.pack(side="right",pady=5)

        # ---------------- Right panel: figure ----------------
        right = tk.Frame(master)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.fig, self.ax = plt.subplots(figsize=(7,4))
        self.canvas = FigureCanvasTkAgg(self.fig, master=right)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Mouse interactions
        self.press_x = None
        self.canvas.mpl_connect("button_press_event", self.on_press)
        self.canvas.mpl_connect("button_release_event", self.on_release)
        self.canvas.mpl_connect("motion_notify_event", self.on_move)
        self.canvas.mpl_connect("scroll_event", self.on_scroll)

        # ---------------- Internal state ----------------
        self.df = None
        self.x_col = None
        self.y_col = None
        self.missing_positions = []
        self.pos_idx = 0
        self.current_type = None
        self.current_index = None
        self.group_start = None
        self.group_end = None
        self.interpolated_indices = set()
        self.vmarker = None
        self.history = []
        self.filename = ""

    # ---------------- Mouse interactions ----------------

    def on_tab_change(self, event):
        tab = event.widget.select()
        tab_text = event.widget.tab(tab, "text")

        if not (self.df is None):
            if tab_text == "Outliers":
                self.start_traitement_outliers()

            if tab_text == "Trous":
                self.entry_inf.delete(0, tk.END)
                self.entry_sup.delete(0, tk.END)
                self.start_missing_process()

    def on_press(self, event): 
        if event.inaxes: self.press_x = event.xdata
    
    def on_release(self, event): self.press_x = None
    
    def on_move(self, event):
        if self.press_x is None or event.inaxes is None: return
        dx = self.press_x - event.xdata
        xmin, xmax = self.ax.get_xlim()
        self.ax.set_xlim(xmin+dx, xmax+dx)
        self.canvas.draw()
    
    def on_scroll(self, event):
        if event.inaxes is None: return
        base_scale = 0.7 if event.button=='up' else 1.3
        xlim = self.ax.get_xlim()
        xc = event.xdata
        new_left = xc-(xc-xlim[0])*base_scale
        new_right = xc+(xlim[1]-xc)*base_scale
        self.ax.set_xlim(new_left,new_right)
        self.canvas.draw()

    # ---------------- File loading ----------------
    def select_file(self):
        filename = filedialog.askopenfilename(filetypes=[("CSV files","*.csv")])
        if filename: self.load_file(filename)

    def load_file(self, filename):
        self.filename = filename.split("/")[-1]
        try: self.df = pd.read_csv(filename)
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de charger le fichier : {e}")
            return
        if len(self.df.columns)!=2:
            messagebox.showerror("Erreur", "Le fichier doit contenir deux colonnes.")
            return
        self.x_col = self.df.columns[0]
        self.y_col = self.df.columns[1]
        self.interpolated_indices.clear()
        self.history=[f"Fichier chargé : {filename} \n"]
        self.draw_full_figure()
        self.update_stats()

    def recompute_missing_positions(self, prev_index_processed=None):
        prev=prev_index_processed
        self.missing_positions = sorted(self.df[self.df[self.y_col].isna()].index.tolist())
        if prev is None: 
            self.pos_idx=0
        else:
            self.pos_idx=0
            for i,p in enumerate(self.missing_positions):
                if p>=prev:
                    self.pos_idx=i
                    break
            else: self.pos_idx=len(self.missing_positions)

    # ---------------- Statistics ----------------
    def update_stats(self):
        if self.df is None:
            return
        else:
            self.df_stats = self.df[self.y_col].describe()
            self.units = self.y_col.split('(')[-1].split(')')[0]

            self.starting_date_value.config(text=str(self.df.iloc[0,0]))
            self.ending_date_value.config(text=str(self.df.iloc[-1,0]))
            self.mean_value.config(text=f"{self.df_stats['mean']:.2f} {self.units}")
            self.std_value.config(text=f"{self.df_stats['std']:.2f} {self.units}")
            self.dt_value.config(text=f"{(pd.to_datetime(self.df.iloc[1,0]) - pd.to_datetime(self.df.iloc[0,0])).total_seconds():n} secondes") # Ensure that it's an integer !

    # ---------------- Drawing ----------------
    def draw_full_figure(self):
        self.ax.clear()
        self.ax.set_title(f"Données de {self.y_col}")
        self.ax.set_xlabel(self.x_col)
        self.ax.set_ylabel(self.y_col)
        self.ax.plot(self.df[self.x_col], self.df[self.y_col], marker='o', linestyle='-')
        self.ax.set_xticks((self.df[self.x_col].iloc[0], self.df[self.x_col].iloc[len(self.df)//2] , self.df[self.x_col].iloc[-1]))
        
        if self.interpolated_indices:
            xs=sorted(self.interpolated_indices)
            ys=[self.df.loc[i,self.y_col] for i in xs]
            self.ax.scatter(xs,ys,color='red',s=50)
        self.canvas.draw()

    def draw_current(self, start, end=None):
        self.draw_full_figure()
        if end is None:
            self.vmarker=self.ax.axvline(x=start,color='red',linestyle='--')
            self.ax.set_xlim(start-30,min(len(self.df)-1,start+30))
        else:
            self.ax.axvspan(start,end,color='red',alpha=0.2)
            self.ax.set_xlim(start-30,min(len(self.df)-1,end+30))
        self.canvas.draw()

    def preview_selection(self, event=None):
        """Affiche en surbrillance sur la figure la plage sélectionnée
        dans sup_label et inf_label sans modifier les données."""
        
        if self.df is None:
            return

        borne_sup_str = self.entry_sup.get().strip()
        borne_inf_str = self.entry_inf.get().strip()

        # Si rien n'est entré → réafficher les données normales
        if borne_sup_str == '' and borne_inf_str == '':
            self.draw_full_figure()
            return

        # Conversions si disponibles
        borne_sup = float(borne_sup_str) if borne_sup_str else None
        borne_inf = float(borne_inf_str) if borne_inf_str else None

        # Conditions rejetées
        if borne_sup < borne_inf:
            self.entry_inf.delete(0, tk.END)
            self.entry_sup.delete(0, tk.END)
            messagebox.showerror("Erreur", "Les bornes sont invalides. Entrez des bornes valides !")
            return

        # Affichage principal
        self.draw_full_figure()

        # Détermination des indices sélectionnés
        if borne_sup is not None and borne_inf is not None:
            self.ax.axhspan(borne_inf,borne_sup,color='red',alpha=0.2)
        elif borne_sup is not None:
            self.ax.axhline(borne_sup,color='red',alpha=0.2)
        else:
            self.ax.axhline(borne_inf,color='red',alpha=0.2)

        self.canvas.draw_idle()

    # ---------------- Manual entry ----------------
    def hide_manual_entry(self):
        self.manual_entry_label.pack_forget()
        self.manual_entry.pack_forget()
        self.manual_entry_button.pack_forget()

    def handle_manual_value(self):
        idx=self.current_index
        val_str=self.manual_entry.get()
        try: val=float(val_str)
        except ValueError:
            messagebox.showerror("Erreur","Veuillez entrer un nombre valide.")
            return
        self.df.loc[idx,self.y_col]=val
        self.interpolated_indices.add(idx)
        self.history.append(f"Valeur manuelle saisie à {idx} : {val}")
        self.hide_manual_entry()
        self.pos_idx+=1
        self.draw_full_figure()
        self.next_missing()

    # ---------------- Iteration for TAB1 ----------------
    def next_missing(self):
        # remove previous marker
        if self.vmarker is not None:
            try: self.vmarker.remove()
            except: pass
            self.vmarker = None

        n = len(self.missing_positions)
        if self.pos_idx >= n:
            self.question_label.config(text="Traitement terminé, n'oubliez pas de sauvegarder les données !")
            self.yes_button.pack_forget()
            self.no_button.pack_forget()
            self.hide_manual_entry()
            return

        start = self.missing_positions[self.pos_idx]
        j = self.pos_idx
        while j + 1 < n and self.missing_positions[j+1] == self.missing_positions[j]+1: 
            j += 1
        end = self.missing_positions[j]
        group_len = end - start + 1

        # BOUNDARY
        if start == 0 or end == len(self.df)-1:
            self.current_type = "boundary"
            self.group_start = start
            self.group_end = end
            self.draw_current(start, end if group_len>1 else None)
            self.question_label.config(text=f"Trou en bordure entre le {self.df[self.x_col][start]} et le {self.df[self.x_col][end]}. Supprimer ?")
            self.yes_button.pack(side="left",padx=5)
            self.no_button.pack(side="right",padx=5)
            self.hide_manual_entry()
            return

        # ISOLATED
        elif group_len == 1:
            self.current_type = "isolated"
            self.current_index = start
            self.draw_current(start)
            self.question_label.config(text=f"Valeur isolée à {self.df[self.x_col][start]}. Interpolation linéaire")
            self.yes_button.pack(side="left",padx=5)
            self.no_button.pack(side="right",padx=5)
            self.manual_entry_label.pack(pady=5)
            self.manual_entry.pack(pady=5)
            self.manual_entry_button.pack(pady=5)
            self.manual_entry.delete(0, tk.END)
            return

        # GROUP <= 4
        elif group_len <= 4:
            prev_idx = start - 1
            next_idx = end + 1
            if pd.isna(self.df.loc[prev_idx, self.y_col]) or pd.isna(self.df.loc[next_idx, self.y_col]):
                # can't interpolate, skip
                self.pos_idx = j + 1
                self.next_missing()
                return

            self.current_type = "group <= 4"
            self.group_start = start
            self.group_end = end
            self.draw_current(start, end)
            self.question_label.config(text=f"Trous entre le {self.df[self.x_col][start]} et le {self.df[self.x_col][end]}. Effectuer une interpolation linéaire ?")
            self.yes_button.pack(side="left",padx=5)
            self.no_button.pack(side="right",padx=5)
            self.hide_manual_entry()

        # GROUP > 4
        elif group_len > 4:
            prev_idx = start - 1
            next_idx = end + 1
            if pd.isna(self.df.loc[prev_idx, self.y_col]) or pd.isna(self.df.loc[next_idx, self.y_col]):
                
                # can't interpolate, skip
                self.pos_idx = j + 1
                self.next_missing()
                return

            self.current_type = "group > 4"
            self.group_start = start
            self.group_end = end
            self.draw_current(start, end)
            self.question_label.config(text="WHAT TO DO ")
            self.next_missing() # For now, we just skip these big groups
            """
            self.yes_button.pack(side="left",padx=5)
            self.no_button.pack(side="right",padx=5)
            self.hide_manual_entry()
            """

    def start_missing_process(self):
        if self.df is None:
            messagebox.showwarning("Attention", "Aucun fichier chargé.")
            return

        self.history.append("Correction des trous : \n")
        self.recompute_missing_positions()
        self.welcome_text.pack_forget()
        self.next_missing()

    # ---------------- Handle answer ----------------
    def handle_answer(self, accept):
        # Is a switch condition
        match self.current_type:
            # BOUNDARY
            case "boundary":
                start,end = self.group_start, self.group_end
                if accept:
                    self.history.append(f"Supprimé la bordure depuis {self.df[self.x_col][start]} jusqu'à {self.df[self.x_col][end]}")
                    self.df = self.df.drop(index=range(start,end+1)).reset_index(drop=True)
                    self.recompute_missing_positions(prev_index_processed=start)
                else:
                    self.history.append(f"Bordure depuis {self.df[self.x_col][start]} jusqu'à {self.df[self.x_col][end]} ignorée")
                self.yes_button.pack_forget()
                self.no_button.pack_forget()
                self.hide_manual_entry()
                self.draw_full_figure()
                self.next_missing()
                return

            # ISOLATED
            case "isolated":
                idx = self.current_index
                if accept:
                    prev = self.df.loc[idx-1,self.y_col]
                    nextv = self.df.loc[idx+1,self.y_col]
                    val = prev + 0.5*(nextv-prev)
                    self.df.loc[idx,self.y_col] = val
                    self.history.append(f"Interpolation isolée à {self.df[self.x_col][idx]} : {val}")
                    self.interpolated_indices.add(idx)
                else:
                    self.history.append(f"Valeur isolée ignorée à {self.df[self.x_col][idx]}")
                self.pos_idx += 1
                self.yes_button.pack_forget()
                self.no_button.pack_forget()
                self.hide_manual_entry()
                self.draw_full_figure()
                self.next_missing()
                return

            # GROUP
            case "group <= 4":
                start, end = self.group_start, self.group_end
                L = end - start + 1
                if accept:
                    prev = self.df.loc[start-1, self.y_col]
                    nextv = self.df.loc[end+1, self.y_col]
                    self.history.append(f"Interpolation linéaire entre {self.df[self.x_col][start-1]} et {self.df[self.x_col][end+1]} :")
                    for i, idx in enumerate(range(start, end+1)):
                        val = prev + (i+1)/(L+1)*(nextv - prev)
                        self.df.loc[idx, self.y_col] = val
                        self.interpolated_indices.add(idx)
                        self.history.append(f"Interpolation valeur {self.df[self.x_col][idx]} → {val}")
                    self.history.append("")
                else:
                    self.history.append(f"Groupe depuis {self.df[self.x_col][start]} jusqu'à {self.df[self.x_col][end]} ignoré")
                
                # AVANCER pos_idx après tout le groupe
                self.pos_idx = self.pos_idx + L
                self.yes_button.pack_forget()
                self.no_button.pack_forget()
                self.hide_manual_entry()
                self.draw_full_figure()
                self.next_missing()
                return

            # GROUP with size > 4
            case "group > 4":
                start, end = self.group_start, self.group_end
                L = end - start + 1
                if accept:
                    prev = self.df.loc[start-1, self.y_col]
                    nextv = self.df.loc[end+1, self.y_col]
                    self.history.append(f"Interpolation faite entre {self.df[self.x_col][start-1]} et {self.df[self.x_col][end+1]} :")
                    for i, idx in enumerate(range(start, end+1)):
                        val = prev + (i+1)/(L+1)*(nextv - prev)
                        self.df.loc[idx, self.y_col] = val
                        self.interpolated_indices.add(idx)
                        self.history.append(f"Interpolation valeur {self.df[self.x_col][idx]} → {val}")
                    self.history.append("")
                else:
                    self.history.append(f"Groupe depuis {self.df[self.x_col][start]} jusqu'à {self.df[self.x_col][end]} ignoré")
            
                # AVANCER pos_idx après tout le groupe
                self.pos_idx = self.pos_idx + L
                self.yes_button.pack_forget()
                self.no_button.pack_forget()
                self.hide_manual_entry()
                self.draw_full_figure()
                self.next_missing()
                return

    # ---------------- Function TAB2 ----------------

    def start_traitement_outliers(self):
        if self.df is None:
            messagebox.showwarning("Attention", "Aucun fichier chargé.")
            return

        self.show_tab2()
        self.remove_selected_range()
        self.welcome_text2.pack_forget()
        self.history.append("Traitement des outliers : \n")

    def show_tab2(self):
        if not self.tab2_tools_visible:
            self.sup_label.pack(pady=(10,0))
            self.entry_sup.pack(pady=5)
            self.inf_label.pack(pady=(10,0))
            self.entry_inf.pack(pady=5)
            self.remove_range_button.pack(pady=15)

    def remove_selected_range(self):
        
        # Check if a file is loaded
        if self.df is None:
            messagebox.showwarning("Attention", "Aucun fichier chargé.")
            return

        # Show tools the first time without warning
        if self.tab2_tools_visible == False:
            self.tab2_tools_visible = True
            return

        borne_sup = float(self.entry_sup.get().strip())
        borne_inf = float(self.entry_inf.get().strip())

        if borne_inf < self.df.min()[self.y_col]:
            borne_inf = self.df.min()[self.y_col]
            messagebox.showinfo("Info", f"La borne inférieure a été ajustée à {borne_inf} (valeur minimale des données).")
            self.entry_inf.config(text=str(borne_inf))

        if borne_sup > self.df.max()[self.y_col]:
            borne_sup = self.df.max()[self.y_col]
            messagebox.showinfo("Info", f"La borne supérieure a été ajustée à {borne_sup} (valeur maximale des données).")
            self.entry_sup.config(text=str(borne_sup))

        if borne_inf > borne_sup:
            messagebox.showerror("Erreur", "Les bornes sont invalides.")
            return

        # Suppression de la plage
        removed_rows = self.df[(self.df[self.y_col] < borne_inf) | (self.df[self.y_col] > borne_sup)].index.tolist()
        self.df.iloc[removed_rows,1] = None

        # Réindexation propre
        self.df = self.df.reset_index(drop=True)

        # Ajout à l'historique
        if borne_inf == self.df.min()[self.y_col]:
            self.history.append(f"Valeurs entre {borne_inf} (minimum) et {borne_sup} sont conservées.")
        elif borne_sup == self.df.max()[self.y_col]:
            self.history.append(f"Valeurs entre {borne_inf} et {borne_sup} (maximum) sont conservées.")
        else:
            self.history.append(f"Valeurs entre {borne_inf} et {borne_sup} sont conservées.")

        # To add a separation line in the history for better readability
        self.history.append("")

        # Mise à jour du graphe
        self.draw_full_figure()

        # Confirmation
        messagebox.showinfo("OK", f"Valeurs entre {borne_inf} et {borne_sup} sont conservées.")

    # ---------------- Save ----------------
    def save_csv(self):
        if self.df is None:
            messagebox.showwarning("Attention","Aucun fichier chargé.")
            return
        
        filename=filedialog.asksaveasfilename(initialdir=os.getcwd(), initialfile=self.filename , filetypes=[("CSV files","*.csv")])
        
        if not filename: 
            messagebox.showerror("Erreur","Donner un nom de fichier valide !")
            return
        
        if filename.endswith(".csv"):
            self.df.to_csv(filename,sep=";",index=False)
            hist_file = filename.replace(".csv","_historique.txt")
        else:
            self.df.to_csv(filename+".csv",sep=";",index=False)
            hist_file = filename+"_historique.txt"
        
        try:
            with open(hist_file,"w",encoding="utf-8") as f:
                for line in self.history: f.write(line+"\n")
        except Exception as e:
            messagebox.showerror("Erreur",f"Impossible d’enregistrer l’historique : {e}")
            return
        messagebox.showinfo("OK",f"Fichier sauvegardé à cette adresse : \"{filename}\" \n \n L'historique a été sauvegardé à cette adresse : \"{hist_file}\"")
        
    def savefig(self):
        if self.df is None:
            messagebox.showwarning("Attention","Aucun fichier chargé.")
        else:
            filename=filedialog.asksaveasfilename(initialdir=os.getcwd(), initialfile=self.filename, filetypes=[("JPEG files","*.jpg"), ("PNG files","*.png")])
            if not filename: 
                messagebox.showerror("Erreur","Donner un nom de fichier valide !")
                return
            self.fig.savefig(filename,format="jpg")
            messagebox.showinfo("OK",f"Figure sauvegardée : \"{filename}\"")

# ---------------- Main loop ----------------

if __name__=="__main__":
    root=tk.Tk()
    app=CSVEditorApp(root)
    root.mainloop()