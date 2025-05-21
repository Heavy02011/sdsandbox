import yaml
import random
import matplotlib.pyplot as plt
import numpy as np
import os
import datetime # Hinzugefügt

CONFIG_FILE = '/workspaces/sdsandbox/notebook/config.yaml'

def load_config():
    """Lädt die Konfiguration aus der YAML-Datei."""
    try:
        with open(CONFIG_FILE, 'r') as f:
            config_data = yaml.safe_load(f)
        if config_data is None:
            print(f"Warnung: Konfigurationsdatei {CONFIG_FILE} ist leer. Verwende Standardwerte.")
            return get_default_config()
        # Sicherstellen, dass die Beispielpfade absolut sind oder relativ zum Notebook-Verzeichnis korrekt aufgelöst werden
        # Da das Skript selbst im Notebook-Verzeichnis liegt, können relative Pfade für tracks/ problematisch sein,
        # wenn das Notebook aus einem anderen Arbeitsverzeichnis gestartet wird.
        # Besser ist es, absolute Pfade zu verwenden oder Pfade relativ zum Skript selbst zu bilden.
        # Hier gehen wir davon aus, dass die Pfade in config.yaml bereits korrekt sind (z.B. absolut).
        return config_data
    except FileNotFoundError:
        print(f"Warnung: Konfigurationsdatei {CONFIG_FILE} nicht gefunden. Verwende Standardwerte.")
        return get_default_config()
    except Exception as e:
        print(f"Fehler beim Laden der Konfiguration {CONFIG_FILE}: {e}. Verwende Standardwerte.")
        return get_default_config()

def get_default_config():
    """Gibt eine Standardkonfiguration zurück."""
    return {
        'track_width': 0.8,
        'segment_length': 5.0,
        'turn_angle_max': 45,
        'num_segments_random': 20,
        'color_centerline': 'black',
        'color_left_border': 'blue',
        'color_right_border': 'red',
        'alternating_colors_segments': ['lightgrey', 'darkgrey'],
        'csv_delimiter': ',',
        'script_path_example': '/workspaces/sdsandbox/notebook/tracks/scripted_track1.txt',
        'csv_path_example': '/workspaces/sdsandbox/notebook/tracks/centerline1.csv'
    }

config = load_config()

# Stelle sicher, dass die Beispielpfade in der Konfiguration vorhanden sind
if 'script_path_example' not in config:
    config['script_path_example'] = get_default_config()['script_path_example']
if 'csv_path_example' not in config:
    config['csv_path_example'] = get_default_config()['csv_path_example']


def generate_random_track(closed_track=False): # Parameter hinzugefügt
    """Generiert einen zufälligen Track, optional geschlossen."""
    track_points = [(0, 0)]
    current_angle = 0
    num_segments = config.get('num_segments_random', 20)
    segment_len = config.get('segment_length', 5.0)
    max_angle = config.get('turn_angle_max', 45)

    for _ in range(num_segments):
        turn_angle = random.uniform(-max_angle, max_angle)
        current_angle += np.deg2rad(turn_angle)
        dx = segment_len * np.cos(current_angle)
        dy = segment_len * np.sin(current_angle)
        new_point = (track_points[-1][0] + dx, track_points[-1][1] + dy)
        track_points.append(new_point)
    
    if closed_track and len(track_points) > 1:
        # Füge den ersten Punkt am Ende hinzu, um den Track zu schließen
        # Dies ist eine einfache Methode. Für eine glatte Schließung wären komplexere Algorithmen nötig,
        # z.B. Anpassung der letzten Segmente oder Spline-Interpolation zum Startpunkt.
        track_points.append(track_points[0])
        print("Zufälliger Track wurde geschlossen.")

    return track_points

def load_scripted_track(script_path, closed_track=False): # Parameter hinzugefügt
    """Lädt einen Track aus einer Skriptdatei (jede Zeile "x y"), optional geschlossen."""
    track_points = []
    try:
        with open(script_path, 'r') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) == 2:
                    try:
                        x, y = float(parts[0]), float(parts[1])
                        track_points.append((x, y))
                    except ValueError:
                        print(f"Ungültige Zeile im Skript übersprungen: {line.strip()}")
    except FileNotFoundError:
        print(f"Skriptdatei nicht gefunden: {script_path}")
        return []
    
    if closed_track and track_points and track_points[0] != track_points[-1]:
        track_points.append(track_points[0])
        print(f"Skriptbasierter Track ({script_path}) wurde geschlossen.")
        
    return track_points

def load_csv_track(csv_path, closed_track=False): # Parameter hinzugefügt
    """Lädt einen Track aus einer CSV-Datei (Mittellinie), optional geschlossen."""
    track_points = []
    try:
        with open(csv_path, 'r') as f:
            header = next(f, None) # Header lesen und überspringen
            if header is None:
                print(f"CSV-Datei ist leer: {csv_path}")
                return []
            for line_number, line in enumerate(f, 1):
                parts = line.strip().split(config.get('csv_delimiter', ','))
                if len(parts) >= 2:
                    try:
                        x, y = float(parts[0]), float(parts[1])
                        track_points.append((x, y))
                    except ValueError:
                        print(f"Ungültige Zeile {line_number+1} in CSV übersprungen: {line.strip()}")
    except FileNotFoundError:
        print(f"CSV-Datei nicht gefunden: {csv_path}")
        return []
    except Exception as e:
        print(f"Fehler beim Lesen der CSV-Datei {csv_path}: {e}")
        return []

    if closed_track and track_points and track_points[0] != track_points[-1]:
        track_points.append(track_points[0])
        print(f"CSV-basierter Track ({csv_path}) wurde geschlossen.")

    return track_points

def get_track_borders(centerline_points):
    """Berechnet die linke und rechte Begrenzung eines Tracks."""
    left_border = []
    right_border = []
    if not centerline_points or len(centerline_points) < 2:
        print("Mittellinie hat nicht genügend Punkte für die Grenzberechnung.")
        return [], []

    track_w = config.get('track_width', 0.8)

    for i in range(len(centerline_points)):
        p_curr = centerline_points[i]

        if i == 0: # Erster Punkt
            p_next = centerline_points[i+1]
            dx, dy = p_next[0] - p_curr[0], p_next[1] - p_curr[1]
        elif i == len(centerline_points) - 1: # Letzter Punkt
            p_prev = centerline_points[i-1]
            dx, dy = p_curr[0] - p_prev[0], p_curr[1] - p_prev[1]
        else: # Mittlere Punkte
            p_prev, p_next = centerline_points[i-1], centerline_points[i+1]
            # Vektor von p_prev zu p_next für eine glattere Normale an Kurvenpunkten
            dx_segment, dy_segment = p_next[0] - p_prev[0], p_next[1] - p_prev[1]
            # Die Normale wird auf diesen Segmentvektor berechnet
            # Der Punkt selbst ist p_curr
            dx, dy = dx_segment, dy_segment


        norm_dx, norm_dy = -dy, dx # Orthogonaler Vektor
        length = np.sqrt(norm_dx**2 + norm_dy**2)

        if length == 0: # Fallback, falls Punkte identisch sind
            if left_border: # Nutze die vorherige Normale (vereinfacht)
                # Dies ist eine Vereinfachung und könnte bei scharfen Kehren ungenau sein
                prev_l_point = left_border[-1]
                prev_c_point = centerline_points[i-1] # Muss i-1 sein
                norm_vec_prev_dx = prev_l_point[0] - prev_c_point[0]
                norm_vec_prev_dy = prev_l_point[1] - prev_c_point[1]
                # Normalisiere diesen Vektor, um die Richtung zu bekommen
                dist_prev = np.sqrt(norm_vec_prev_dx**2 + norm_vec_prev_dy**2)
                if dist_prev > 0:
                    norm_dx_normalized = (norm_vec_prev_dx / dist_prev)
                    norm_dy_normalized = (norm_vec_prev_dy / dist_prev)
                else: # Sollte nicht passieren
                    norm_dx_normalized, norm_dy_normalized = 0, 1

            else: # Kein vorheriger Punkt, Standard-Fallback
                norm_dx_normalized, norm_dy_normalized = 0, 1
        else:
            norm_dx_normalized, norm_dy_normalized = norm_dx / length, norm_dy / length

        left_x = p_curr[0] + norm_dx_normalized * track_w / 2
        left_y = p_curr[1] + norm_dy_normalized * track_w / 2
        left_border.append((left_x, left_y))

        right_x = p_curr[0] - norm_dx_normalized * track_w / 2
        right_y = p_curr[1] - norm_dy_normalized * track_w / 2
        right_border.append((right_x, right_y))

    return left_border, right_border


def plot_track(centerline, left_border, right_border, save_path_prefix=None): # save_path_prefix hinzugefügt
    """Stellt den Track mit Rändern und Segmentfarben dar und speichert ihn optional."""
    plt.style.use('seaborn-v0_8-whitegrid')
    fig = plt.figure(figsize=(16, 10)) # fig zugewiesen, um savefig verwenden zu können

    # Segmente mit alternierenden Farben füllen
    colors = config.get('alternating_colors_segments', ['#e0e0e0', '#c0c0c0']) # Hellere Grautöne
    if len(centerline) > 1 and len(left_border) > 1 and len(right_border) > 1:
        for i in range(len(centerline) - 1):
            x_coords = [left_border[i][0], right_border[i][0], right_border[i+1][0], left_border[i+1][0]]
            y_coords = [left_border[i][1], right_border[i][1], right_border[i+1][1], left_border[i+1][1]]
            plt.fill(x_coords, y_coords, color=colors[i % len(colors)], alpha=0.7, edgecolor='grey', linewidth=0.5, zorder=0)

    # Mittellinie
    if centerline:
        cx, cy = zip(*centerline)
        plt.plot(cx, cy, color=config.get('color_centerline', 'black'), linewidth=2.5, linestyle='--', label='Mittellinie', zorder=3)

    # Linke und rechte Begrenzung
    line_width_border = 4.5 # Dickere Linien für "gigantisch"
    shadow_alpha = 0.4
    shadow_offset = 0.03 # Kleinerer Offset für subtileren Schatten

    if left_border:
        lx, ly = zip(*left_border)
        # Schatten für linken Rand
        plt.plot(np.array(lx) + shadow_offset, np.array(ly) - shadow_offset, color='#555599', linewidth=line_width_border + 0.5, zorder=1, alpha=shadow_alpha)
        plt.plot(lx, ly, color=config.get('color_left_border', 'blue'), linewidth=line_width_border, label='Linker Rand', zorder=2)


    if right_border:
        rx, ry = zip(*right_border)
        # Schatten für rechten Rand
        plt.plot(np.array(rx) + shadow_offset, np.array(ry) - shadow_offset, color='#995555', linewidth=line_width_border + 0.5, zorder=1, alpha=shadow_alpha)
        plt.plot(rx, ry, color=config.get('color_right_border', 'red'), linewidth=line_width_border, label='Rechter Rand', zorder=2)

    plt.title('Generierter Track', fontsize=26, fontweight='bold', color='#333333')
    plt.xlabel('X-Koordinate', fontsize=18, color='#444444')
    plt.ylabel('Y-Koordinate', fontsize=18, color='#444444')
    plt.legend(fontsize=14, loc='best', frameon=True, shadow=True)
    plt.axis('equal')
    plt.grid(True, linestyle=':', alpha=0.7, color='darkgray')
    plt.gca().set_facecolor('#fafafa') # Sehr heller Hintergrund
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    plt.tight_layout() # Passt Plot an Fenstergröße an

    if save_path_prefix:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{save_path_prefix}_track_{timestamp}.png"
        try:
            # Stelle sicher, dass das Verzeichnis für den Speicherpfad existiert
            output_dir = os.path.dirname(filename)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
                print(f"Verzeichnis erstellt: {output_dir}")
            fig.savefig(filename, dpi=300) # fig.savefig statt plt.savefig
            print(f"Track gespeichert als: {filename}")
        except Exception as e:
            print(f"Fehler beim Speichern des Tracks als PNG: {e}")
    
    plt.show()

def ensure_example_files():
    """Erstellt Beispiel-Skript- und CSV-Dateien, falls nicht vorhanden."""
    base_path = os.path.dirname(config.get('script_path_example', get_default_config()['script_path_example'])) # /notebook/tracks

    if not os.path.exists(base_path):
        try:
            os.makedirs(base_path)
            print(f"Verzeichnis {base_path} erstellt.")
        except OSError as e:
            print(f"Fehler beim Erstellen des Verzeichnisses {base_path}: {e}")
            return

    default_script_path = config.get('script_path_example')
    if default_script_path and not os.path.exists(default_script_path):
        try:
            with open(default_script_path, 'w') as f:
                f.write("0 0\n10 5\n20 0\n30 -5\n25 -15\n15 -10\n5 -8\n0 -5\n-5 -2\n0 0\n") # Geschlossener Track
            print(f"Beispiel-Skriptdatei erstellt: {default_script_path}")
        except Exception as e:
            print(f"Fehler beim Erstellen der Beispiel-Skriptdatei {default_script_path}: {e}")

    default_csv_path = config.get('csv_path_example')
    if default_csv_path and not os.path.exists(default_csv_path):
        try:
            with open(default_csv_path, 'w') as f:
                f.write("x,y,comment\n")
                f.write("0,0,start_node\n5,2,node1\n10,5,node2\n15,3,node3\n20,0,node4\n25,-2,node5\n20,-5,node6\n10,-6,node7\n0,-3,end_node\n")
            print(f"Beispiel-CSV-Datei erstellt: {default_csv_path}")
        except Exception as e:
            print(f"Fehler beim Erstellen der Beispiel-CSV-Datei {default_csv_path}: {e}")

# Beim Import des Moduls sicherstellen, dass die Beispieldateien existieren
ensure_example_files()

print("trackgenlib.py wurde initialisiert und Konfiguration geladen.")
print(f"Konfiguration: track_width={config.get('track_width')}, script_example='{config.get('script_path_example')}', csv_example='{config.get('csv_path_example')}'")
