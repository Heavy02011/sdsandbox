import yaml
import math # Für Kreisberechnungen
import random # Für Zufallswerte
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
        'turn_angle_max': 45, # Für 'straight_turn'
        'num_segments_random': 20,
        'color_centerline': 'black',
        'color_left_border': 'blue',
        'color_right_border': 'red',
        'alternating_colors_segments': ['lightgrey', 'darkgrey'],
        'csv_delimiter': ',',
        'script_path_example': '/workspaces/sdsandbox/notebook/tracks/scripted_track1.txt',
        'csv_path_example': '/workspaces/sdsandbox/notebook/tracks/centerline1.csv',
        # Neue Parameter für zufällige Trackgenerierung mit Bögen
        'curve_types_random': ['straight_turn', 'arc'], # Mögliche Segmenttypen
        'arc_radius_min': 5.0,                             # Minimaler Radius für einen Bogen
        'arc_radius_max': 20.0,                            # Maximaler Radius für einen Bogen
        'arc_angle_max': 90.0,                             # Maximaler Winkel (in Grad) für ein Bogensegment
        'arc_num_points': 10,                              # Anzahl der Punkte zur Approximation eines Bogens
        'max_closing_length_factor': 1.5,                  # Maximales Verhältnis der Schließungslänge zur durchschnittlichen Segmentlänge
        # Standardparameter für polare Track-Generierung
        'polar_angles_fixed': [0, 90, 180, 270],                 # Winkel in Grad zur Erzeugung der Mittellinie
        'polar_distances_fixed': [10, 10, 10, 10],               # Abstände vom Ursprung für polaren Track
        'polar_angle_range_random': [0, 360],                 # Winkelbereich in Grad für zufällige Polarwinkel
        'polar_distance_range_random': [5, 20],               # Abstandsbereich für zufällige Polarabstände
        'num_points_polar_random': 10,                        # Anzahl der Punkte für zufällige polare Tracks
        'smoothing_window': 1                              # Fenstergröße für gleitenden Durchschnitt (1 = kein Smoothing)
    }

config = load_config()

# Stelle sicher, dass die Beispielpfade und neuen Kurvenparameter in der Konfiguration vorhanden sind
# Diese Validierung kann verfeinert oder entfernt werden, wenn die config.yaml als "source of truth" gilt.
default_conf = get_default_config() # Wird ggf. nicht mehr benötigt, wenn alles aus config kommt
for key in ['script_path_example', 'csv_path_example', 
            'curve_types_random', 'arc_radius_min', 'arc_radius_max', 
            'arc_angle_max', 'arc_num_points', 'max_closing_length_factor',
            'polar_angles_fixed', 'polar_distances_fixed', # Angepasst an neue Namen
            'polar_angle_range_random', 'polar_distance_range_random', # Angepasst an neue Namen
            'num_points_polar_random', 'smoothing_window']: # Fehlende hinzugefügt
    if key not in config:
        # config[key] = default_conf.get(key) # Optional: Fehlende Werte mit Defaults füllen
        print(f"Hinweis: Schlüssel '{key}' nicht in config.yaml gefunden. Standardwert wird verwendet oder es könnte ein Fehler auftreten.")


def generate_random_track(closed_track=False):
    """Generiert einen zufälligen Track, optional geschlossen, mit verschiedenen Segmenttypen."""
    track_points = [(0, 0)]
    current_angle_rad = 0  # Startwinkel 0 (entlang der positiven x-Achse)
    num_segments_total = config.get('num_segments_random', 20)
    
    # Parameter für 'straight_turn'
    segment_len_straight = config.get('segment_length', 5.0)
    max_angle_turn_deg = config.get('turn_angle_max', 45)

    # Parameter für 'arc'
    curve_types = config.get('curve_types_random', ['straight_turn'])
    arc_radius_min = config.get('arc_radius_min', 5.0)
    arc_radius_max = config.get('arc_radius_max', 20.0)
    # arc_angle_max_deg wird als maximaler *Betrag* des Winkels für einen Bogen interpretiert
    arc_angle_total_max_deg = config.get('arc_angle_max', 90.0) 
    arc_num_points_approx = config.get('arc_num_points', 10)

    for i in range(num_segments_total):
        last_x, last_y = track_points[-1]
        
        # Wähle zufällig einen Segmenttyp
        segment_type = random.choice(curve_types)

        if segment_type == 'straight_turn' or not curve_types or 'arc' not in curve_types: # Fallback, falls 'arc' nicht konfiguriert
            # Generiere ein gerades Segment mit einer Kurve (Ecke) am Ende
            turn_angle_deg = random.uniform(-max_angle_turn_deg, max_angle_turn_deg)
            current_angle_rad += math.radians(turn_angle_deg)
            
            new_x = last_x + segment_len_straight * math.cos(current_angle_rad)
            new_y = last_y + segment_len_straight * math.sin(current_angle_rad)
            track_points.append((new_x, new_y))

        elif segment_type == 'arc':
            # Generiere ein Kreisbogensegment
            arc_radius = random.uniform(arc_radius_min, arc_radius_max)
            # Zufälliger Gesamtwinkel für den Bogen (positiv oder negativ)
            arc_total_angle_deg = random.uniform(-arc_angle_total_max_deg, arc_angle_total_max_deg)
            if abs(arc_total_angle_deg) < 1: # Mindestwinkel, um Division durch Null zu vermeiden
                arc_total_angle_deg = math.copysign(1.0, arc_total_angle_deg)

            arc_total_angle_rad = math.radians(arc_total_angle_deg)
            
            # Richtung des Bogens (links oder rechts)
            # Positive arc_total_angle_rad -> Linkskurve
            # Negative arc_total_angle_rad -> Rechtskurve

            # Mittelpunkt des Kreises finden, auf dem der Bogen liegt.
            # Der Mittelpunkt liegt senkrecht zur aktuellen Bewegungsrichtung (current_angle_rad)
            # im Abstand arc_radius.
            # Winkel zum Kreismittelpunkt (senkrecht zur Fahrtrichtung)
            # Bei Linkskurve (arc_total_angle_rad > 0): current_angle_rad + PI/2
            # Bei Rechtskurve (arc_total_angle_rad < 0): current_angle_rad - PI/2
            angle_to_center_rad = current_angle_rad + math.copysign(math.pi / 2, arc_total_angle_rad)
            
            center_x = last_x - arc_radius * math.cos(angle_to_center_rad)
            center_y = last_y - arc_radius * math.sin(angle_to_center_rad)

            # Startwinkel des Bogens relativ zum Kreismittelpunkt
            # Dies ist der Winkel vom Kreismittelpunkt zum letzten Punkt des Tracks
            start_angle_on_circle_rad = angle_to_center_rad + math.pi # Um 180 Grad gedreht

            # Punkte auf dem Bogen generieren
            # arc_num_points_approx ist die Anzahl der *Segmente* des Bogens, also +1 Punkte
            for k in range(1, arc_num_points_approx + 1):
                # Interpolierter Winkel auf dem Bogen
                # Der Winkel inkrementiert von start_angle_on_circle_rad
                # in Richtung von -copysign(1, arc_total_angle_rad) * (k * step)
                # (Vorzeichenumkehr, da der Bogen "zurück" zum Mittelpunkt zeigt)
                
                # Der Winkel des aktuellen Punkts auf dem Kreis, relativ zum Kreismittelpunkt
                # Der Bogen "startet" am letzten Punkt. Der Winkel von diesem Punkt zum Kreismittelpunkt ist
                # current_angle_rad - copysign(PI/2, arc_total_angle_rad).
                # Der Startwinkel des Bogensegments auf dem Kreis ist dieser Winkel.
                # Der Endwinkel ist start_angle_segment_rad + arc_total_angle_rad.
                
                # Startwinkel des Bogens relativ zum Kreismittelpunkt (zeigt vom Mittelpunkt zum letzten Punkt)
                angle_from_center_to_last_point_rad = math.atan2(last_y - center_y, last_x - center_x)

                # Punkte auf dem Bogen generieren
                for point_idx in range(1, arc_num_points_approx + 1):
                    # Anteil des aktuellen Punktes am Gesamtbogen
                    fraction_of_arc = point_idx / arc_num_points_approx
                    # Aktueller Winkel auf dem Kreis für diesen Punkt
                    # Das Vorzeichen von arc_total_angle_rad bestimmt die Drehrichtung
                    current_segment_angle_rad = angle_from_center_to_last_point_rad + fraction_of_arc * arc_total_angle_rad
                    
                    arc_point_x = center_x + arc_radius * math.cos(current_segment_angle_rad)
                    arc_point_y = center_y + arc_radius * math.sin(current_segment_angle_rad)
                    track_points.append((arc_point_x, arc_point_y))

            # Update current_angle_rad für das nächste Segment
            # Die neue Richtung ist die Tangente am Ende des Bogens.
            # Der Winkel vom Mittelpunkt zum letzten Bogenpunkt ist current_segment_angle_rad (bereits berechnet).
            # Die Tangente steht senkrecht dazu.
            # Bei Linkskurve (arc_total_angle_rad > 0): current_segment_angle_rad + PI/2
            # Bei Rechtskurve (arc_total_angle_rad < 0): current_segment_angle_rad - PI/2
            current_angle_rad = current_segment_angle_rad + math.copysign(math.pi / 2, -arc_total_angle_rad) # Vorzeichen umkehren für Tangente

    if closed_track and len(track_points) > 1:
        track_points = close_track_smoothly(track_points)
    return track_points

def generate_polar_track(angles=None, distances=None, smoothing_window_override=None, closed_track=False):
    """Generiert einen Track anhand polaren Koordinaten (Winkel in Grad, Abstand zum Ursprung).

    Parameter:
      angles: Liste von Winkeln in Grad (0–360). Wenn None, werden 'polar_angles_fixed' aus config verwendet.
      distances: Liste von Abständen zum Ursprung. Wenn None, werden 'polar_distances_fixed' aus config verwendet.
      smoothing_window_override: Überschreibt den 'smoothing_window' Wert aus der config.
      closed_track: Bool, ob der Track geschlossen wird.  

    Gibt zurück:
      Liste von (x, y) Koordinaten der Mittellinie."""
    # Standardwerte aus Konfiguration, wenn keine spezifischen übergeben wurden
    # Dies ist für Mode 3 (fester Polar-Track)
    if angles is None:
        angles = config.get('polar_angles_fixed')
    if distances is None:
        distances = config.get('polar_distances_fixed')
        
    # Glättungsfenster: Override hat Vorrang, dann config, dann Default 1
    smoothing_val = smoothing_window_override if smoothing_window_override is not None else config.get('smoothing_window', 1)

    # Validierung
    if not angles or not distances or len(angles) != len(distances):
        print(f"FEHLER in generate_polar_track: Ungültige Winkel ({len(angles) if angles else 'None'}) oder Distanzen ({len(distances) if distances else 'None'}). Müssen Listen gleicher Länge sein.")
        return []
    # 1) Erzeuge Punkte in kartesischen Koordinaten
    track_points = []
    for ang_deg, r in zip(angles, distances):
        ang_rad = np.deg2rad(ang_deg % 360)
        x = r * np.cos(ang_rad)
        y = r * np.sin(ang_rad)
        track_points.append((x, y))
    # 2) Glättung: gleitender Durchschnitt (Smoothing)
    if smoothing_val and smoothing_val > 1 and len(track_points) >= smoothing_val:
        xs = np.array([p[0] for p in track_points])
        ys = np.array([p[1] for p in track_points])
        kernel = np.ones(smoothing_val) / smoothing_val
        xs_smooth = np.convolve(xs, kernel, mode='same')
        ys_smooth = np.convolve(ys, kernel, mode='same')
        track_points = list(zip(xs_smooth.tolist(), ys_smooth.tolist()))
    # 3) Optional sanftes Schließen des Tracks
    if closed_track:
        # Verwende die verbesserte Schließfunktion
        track_points = close_track_smoothly(track_points)
    return track_points


def generate_random_polar_arc_track(angles_deg, distances, closed_track=False):
    """
    Generiert einen zufälligen Polar-Track, der Kreisbogensegmente enthalten kann.
    Die übergebenen Winkel und Distanzen definieren die "Ankerpunkte" des Tracks.
    Zwischen diesen Ankerpunkten können Geraden oder Bögen generiert werden.
    
    Diese Funktion wurde speziell für Mode 4 entwickelt und verwendet entsprechende
    Konfigurationsparameter aus config.yaml (curve_types_polar_random etc.)
    
    Die Implementierung nutzt einen Heading-Vektor-Ansatz, um sicherzustellen, dass die
    Kreisbögen und Segmente mit korrekten Tangenten/Steigungen aneinander anschließen.
    Bei geschlossenen Tracks wird sichergestellt, dass die Steigung am Anfang und Ende übereinstimmt.

    Args:
        angles_deg (list): Liste von Winkeln in Grad.
        distances (list): Liste von Distanzen.
        closed_track (bool): Ob der Track geschlossen werden soll.

    Returns:
        list: Liste von (x, y) Koordinaten der Mittellinie.
    """
    if not angles_deg or not distances or len(angles_deg) != len(distances):
        print("FEHLER in generate_random_polar_arc_track: Ungültige Winkel oder Distanzen.")
        return []

    # Konvertiere Polar-Ankerpunkte zu Kartesischen Koordinaten
    anchor_points_cartesian = []
    for ang_deg, r in zip(angles_deg, distances):
        ang_rad = np.deg2rad(ang_deg % 360)
        x = r * np.cos(ang_rad)
        y = r * np.sin(ang_rad)
        anchor_points_cartesian.append((x, y))

    if not anchor_points_cartesian:
        print("FEHLER in generate_random_polar_arc_track: Keine Ankerpunkte erstellt.")
        return []

    # Für geschlossene Tracks: Füge ersten Punkt am Ende hinzu
    original_anchor_points = anchor_points_cartesian.copy()
    if closed_track:
        anchor_points_cartesian.append(anchor_points_cartesian[0])

    # Erweiterter Ansatz mit Heading-Vektor
    # Initialisierung mit dem ersten Ankerpunkt
    first_point = anchor_points_cartesian[0]
    track_points = [first_point]  # Start mit dem ersten Ankerpunkt
    
    # Berechne initial die Ausrichtung basierend auf den ersten zwei Ankerpunkten
    if len(anchor_points_cartesian) > 1:
        second_point = anchor_points_cartesian[1]
        # Initiale Richtung vom ersten zum zweiten Punkt
        current_heading_rad = math.atan2(second_point[1] - first_point[1], 
                                       second_point[0] - first_point[0])
    else:
        current_heading_rad = 0  # Fallback
    
    # Track-Punkte mit Heading-Vektoren
    point_headings = [(first_point, current_heading_rad)]

    # Parameter für Bögen aus der Konfiguration (Mode 4 spezifisch)
    curve_types = config.get('curve_types_polar_random', ['straight'])
    arc_radius_min = config.get('polar_arc_radius_min', 5.0)
    arc_radius_max = config.get('polar_arc_radius_max', 20.0)
    arc_angle_total_max_deg = config.get('polar_arc_max_angle_deg', 90.0)
    arc_num_points_approx = config.get('polar_arc_num_points', 10)
    
    # Parameter für Kollisionsvermeidung
    min_distance_between_points = arc_radius_min * 0.5
    
    # Generiere den Track punktweise, unter Berücksichtigung der Heading-Vektoren
    for i in range(len(anchor_points_cartesian) - 1):
        current_pos, current_heading_rad = point_headings[-1]
        target_anchor_point = anchor_points_cartesian[i+1]
        
        # 1. Berechne Vektor zum Zielpunkt
        dx_to_target = target_anchor_point[0] - current_pos[0]
        dy_to_target = target_anchor_point[1] - current_pos[1]
        distance_to_target = math.sqrt(dx_to_target**2 + dy_to_target**2)
        angle_to_target_rad = math.atan2(dy_to_target, dx_to_target)
        
        # 2. Berechne Winkelunterschied zum aktuellen Heading
        angle_diff = (angle_to_target_rad - current_heading_rad) % (2 * math.pi)
        if angle_diff > math.pi:
            angle_diff -= 2 * math.pi  # Normalisiere auf [-π, π]
            
        # Wichtig für geschlossene Tracks: Sicherstellen, dass die Steigung am Ende gleich der am Anfang ist
        if closed_track and i == len(anchor_points_cartesian) - 2:
            # Wir müssen sicherstellen, dass die Steigung am Anfang und Ende übereinstimmt
            initial_heading_rad = point_headings[0][1]
            target_heading_rad = initial_heading_rad
            
            # Spezieller Fall, um einen Bogen zu erzeugen, der genau die richtige Ausrichtung am Ende hat
            segment_type = 'arc'
            
            # Berechne den Winkel, den wir überbrücken müssen
            final_heading_diff = (target_heading_rad - current_heading_rad) % (2 * math.pi)
            if final_heading_diff > math.pi:
                final_heading_diff -= 2 * math.pi  # Normalisiere auf [-π, π]
                
            # Berechne einen passenden Bogenradius basierend auf Abstand und Winkel
            # Kleinere Winkel brauchen größere Radien für sanfte Übergänge
            if abs(final_heading_diff) < 0.001:  # Fast gleiche Richtung
                arc_radius = distance_to_target * 2  # Großer Radius für fast gerade Linie
            else:
                # Berechne einen geeigneten Radius, der nicht zu klein und nicht zu groß ist
                # Je größer die zu überbrückende Winkeländerung, desto kleiner der Radius
                desired_angle = abs(final_heading_diff)
                # Vereinfachte Formel für Radius = Distanz / sin(Winkel)
                # Bei kleineren Winkeln wird der Radius größer, aber wir begrenzen ihn
                arc_radius = min(
                    max(
                        arc_radius_min, 
                        distance_to_target / (2 * math.sin(desired_angle/2)) if desired_angle > 0.01 else distance_to_target
                    ),
                    arc_radius_max * 0.7  # 70% des maximalen Radius, um Überlappungen zu vermeiden
                )
                
            # Richtung des Bogens basierend auf kürzestem Weg zum Zielwinkel
            arc_direction = 1 if final_heading_diff > 0 else -1
            # Der Winkel, den der Bogen überstreicht, ist genau final_heading_diff
            arc_total_angle_rad = final_heading_diff
        else:
            # Normale Segment-Typauswahl für nicht-Abschlusssegmente
            # Reduziere die Wahrscheinlichkeit für Bögen auf 20%
            segment_type = random.choice(curve_types) if random.random() > 0.8 else 'straight'
            
            # Bei zu starken Richtungsänderungen erzwinge einen Bogen für natürlicheren Übergang
            if abs(angle_diff) > math.radians(45):
                segment_type = 'arc'
        
        # Segment erzeugen basierend auf dem ausgewählten Typ
        if segment_type == 'straight':
            # Direkte Linie zum Zielpunkt
            new_point = target_anchor_point
            # Aktualisiere das Heading in Richtung des Ziels
            new_heading_rad = angle_to_target_rad
            
            # Füge den neuen Punkt mit seinem Heading hinzu
            track_points.append(new_point)
            point_headings.append((new_point, new_heading_rad))
            
        elif segment_type == 'arc':
            # Für normale Bogensegmente (nicht der letzte Abschluss bei geschlossenen Tracks)
            if not (closed_track and i == len(anchor_points_cartesian) - 2):
                # Berechne den optimalen Radius basierend auf der Distanz zum Ziel und dem Winkelunterschied
                # Bei kleiner Winkeländerung: Größerer Radius für sanftere Kurve
                # Bei großer Winkeländerung: Kleinerer Radius für schärfere Kurve, aber nicht zu klein
                
                # Wenn die Winkeländerung sehr klein ist, verwenden wir eine gerade Linie
                if abs(angle_diff) < math.radians(10):
                    segment_type = 'straight'
                    arc_radius = 0  # wird nicht verwendet
                    arc_total_angle_rad = 0  # wird nicht verwendet
                else:
                    # Bei mittleren bis großen Winkeländerungen: Optimaler Radius
                    # Formula: R = D / (2 * sin(θ/2)) wobei D die Distanz und θ der zu überbrückende Winkel ist
                    # Diese Formel ergibt einen Bogen, der den Zielpunkt genau trifft
                    arc_radius = min(
                        max(
                            arc_radius_min,
                            distance_to_target / (2 * abs(math.sin(angle_diff/2))) if abs(angle_diff) > 0.01 else distance_to_target
                        ),
                        arc_radius_max
                    )
                    
                    # Begrenze die Winkeländerung für natürlichere Kurven
                    max_angle_rad = math.radians(arc_angle_total_max_deg)
                    angle_magnitude = min(abs(angle_diff), max_angle_rad)
                    
                    # Behalte das Vorzeichen bei (links oder rechts abbiegen)
                    arc_direction = 1 if angle_diff > 0 else -1
                    arc_total_angle_rad = angle_magnitude * arc_direction
            
            # Mittelpunkt des Kreisbogens berechnen
            # Bei einem Bogen mit Winkel arc_total_angle_rad muss der Mittelpunkt senkrecht 
            # zur aktuellen Heading-Richtung im Abstand arc_radius liegen
            # Die Richtung hängt vom Vorzeichen des Winkels ab: positiv = links, negativ = rechts
            turn_direction = 1 if arc_total_angle_rad > 0 else -1
            # Wenn wir nach links abbiegen (positiv), liegt der Mittelpunkt links vom aktuellen Heading
            # was +90° entspricht, bei Rechtsabbiegung (negativ) -90°
            perp_angle_to_center = current_heading_rad + (math.pi/2) * turn_direction
            center_x = current_pos[0] + arc_radius * math.cos(perp_angle_to_center)
            center_y = current_pos[1] + arc_radius * math.sin(perp_angle_to_center)
            
            # Winkel vom Kreismittelpunkt zum aktuellen Punkt
            # Das ist der Startwinkel für den Bogen auf dem Kreis
            angle_from_center_to_current = math.atan2(
                current_pos[1] - center_y, 
                current_pos[0] - center_x
            )
            
            # Bogen-Punkte erzeugen
            arc_points = []
            
            # Adaptiere die Anzahl der Bogenpunkte basierend auf der Winkelgröße
            # aber reduziere die Gesamtanzahl und setze ein Maximum
            num_arc_points = max(3, min(8, int(arc_num_points_approx * abs(arc_total_angle_rad) / math.radians(90))))
            
            last_arc_angle = angle_from_center_to_current
            
            for j in range(1, num_arc_points + 1):
                fraction = j / num_arc_points
                # Winkel auf dem Kreisbogen vom Start- zum Endwinkel
                arc_angle = angle_from_center_to_current + fraction * arc_total_angle_rad
                last_arc_angle = arc_angle
                
                # Position auf dem Kreisbogen
                arc_x = center_x + arc_radius * math.cos(arc_angle)
                arc_y = center_y + arc_radius * math.sin(arc_angle)
                arc_point = (arc_x, arc_y)
                
                # Tangentiale Richtung an diesem Punkt auf dem Bogen
                # Die Tangente steht senkrecht zur Linie vom Mittelpunkt zum Punkt auf dem Bogen
                # Der Tangentialwinkel ist der Winkel zum Mittelpunkt + 90° im richtigen Drehsinn
                arc_heading = arc_angle + math.pi/2 * (-turn_direction)
                
                # Punkt zum Track hinzufügen
                arc_points.append(arc_point)
                track_points.append(arc_point)
                point_headings.append((arc_point, arc_heading))
            
            # Spezialbehandlung für das letzte Segment bei geschlossenen Tracks
            if closed_track and i == len(anchor_points_cartesian) - 2:
                # Stelle sicher, dass der Track perfekt geschlossen ist
                # Wir müssen prüfen, ob wir den Zielpunkt wirklich erreicht haben
                # und ob die Tangente am letzten Punkt dem Initial-Heading entspricht
                
                # Für eine glatte Verbindung:
                # 1. Ersetze den letzten Punkt durch den exakten Startpunkt
                if arc_points:  # Wenn Bogenpunkte erzeugt wurden
                    # Ersetze den letzten generierten Punkt mit dem exakten Startpunkt
                    track_points[-1] = track_points[0]
                    
                    # 2. Setze das Heading auf den Initial-Wert zurück
                    point_headings[-1] = (track_points[0], point_headings[0][1])
                    
                    # 3. Optional: Füge einen zusätzlichen Punkt vor dem letzten ein,
                    # um den Übergang noch weicher zu machen
                    if len(arc_points) > 2:
                        # Berechne einen Punkt zwischen dem vorletzten und dem letzten,
                        # der bereits eine Richtung in Richtung des Initial-Headings hat
                        pen_x, pen_y = arc_points[-2]
                        init_heading = point_headings[0][1]
                        
                        # Erzeuge einen Zwischenpunkt mit angepasster Richtung
                        # der zwischen dem vorletzten Bogenpunkt und dem Startpunkt liegt
                        transition_x = (pen_x + track_points[0][0]) / 2
                        transition_y = (pen_y + track_points[0][1]) / 2
                        
                        # Ersetze den vorletzten Punkt
                        if len(track_points) >= 2:
                            track_points[-2] = (transition_x, transition_y)
                            # Setze das Heading zu einem Mittelwert
                            avg_heading = (point_headings[-2][1] + init_heading) / 2
                            point_headings[-2] = ((transition_x, transition_y), avg_heading)

    # Spezielle Glättung für geschlossene Tracks
    smoothing_val = config.get('smoothing_window', 1)
    if smoothing_val and smoothing_val > 1 and len(track_points) >= smoothing_val:
        if closed_track and track_points[0] == track_points[-1]:
            # Erzeuge eine zyklische Kopie für bessere Glättung an den Rändern
            wrap_size = smoothing_val
            xs_cyclical = [p[0] for p in track_points[-(wrap_size+1):-1]] + [p[0] for p in track_points] + [p[0] for p in track_points[1:wrap_size+1]]
            ys_cyclical = [p[1] for p in track_points[-(wrap_size+1):-1]] + [p[1] for p in track_points] + [p[1] for p in track_points[1:wrap_size+1]]
            
            xs = np.array(xs_cyclical)
            ys = np.array(ys_cyclical)
            
            # Anwenden der Glättung
            kernel = np.ones(smoothing_val) / smoothing_val
            xs_smooth = np.convolve(xs, kernel, mode='same')
            ys_smooth = np.convolve(ys, kernel, mode='same')
            
            # Nimm nur den mittleren Teil zurück (ohne die Wrapper-Punkte)
            xs_smooth = xs_smooth[wrap_size:-wrap_size]
            ys_smooth = ys_smooth[wrap_size:-wrap_size]
            
            # Stelle sicher, dass Start- und Endpunkt exakt übereinstimmen
            xs_smooth[-1] = xs_smooth[0]
            ys_smooth[-1] = ys_smooth[0]
            
            # Konvertiere zurück zu einer Liste von Punkten
            track_points = list(zip(xs_smooth.tolist(), ys_smooth.tolist()))
        else:
            # Normale Glättung für nicht geschlossene Tracks
            xs = np.array([p[0] for p in track_points])
            ys = np.array([p[1] for p in track_points])
            
            kernel = np.ones(smoothing_val) / smoothing_val
            xs_smooth = np.convolve(xs, kernel, mode='same')
            ys_smooth = np.convolve(ys, kernel, mode='same')
            
            # Konvertiere zurück zu einer Liste von Punkten
            track_points = list(zip(xs_smooth.tolist(), ys_smooth.tolist()))

    return track_points
def load_scripted_track(script_path, closed_track=False):
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
    
    if closed_track and track_points and (len(track_points) < 2 or track_points[0] != track_points[-1]):
        track_points = close_track_smoothly(track_points)
    return track_points

def load_csv_track(csv_path, closed_track=False):
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

    if closed_track and track_points and (len(track_points) < 2 or track_points[0] != track_points[-1]):
        track_points = close_track_smoothly(track_points)
    return track_points

def get_track_borders(centerline_points):
    """Berechnet die linke und rechte Begrenzung eines Tracks."""
    left_border = []
    right_border = []
    if not centerline_points or len(centerline_points) < 2:
        print("Warnung in get_track_borders: Mittellinie hat weniger als 2 Punkte, Ränder können nicht berechnet werden.")
        return [], []

    track_w = config.get('track_width', 0.8) # Standardwert, falls nicht in config

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


def plot_track(centerline, left_border, right_border, save_path_prefix=None):
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
    
    # Markiere Start- und Endpunkt der Mittellinie, falls vorhanden
    if centerline and len(centerline) > 1:
        start_x, start_y = centerline[0]
        end_x, end_y = centerline[-1]
        
        # Startpunkt: blauer halbtransparenter Kreis
        plt.scatter(start_x, start_y, s=150, color='blue', alpha=0.6, marker='o', zorder=5, label='Start')
        
        # Endpunkt: grüne halbtransparente Raute (Diamond)
        # Bei geschlossenen Tracks sind Start und Ende identisch, also nur anzeigen, wenn sie unterschiedlich sind
        if (start_x, start_y) != (end_x, end_y):
            plt.scatter(end_x, end_y, s=150, color='green', alpha=0.6, marker='D', zorder=5, label='Ende')
    
    # Markiere Start- und Endpunkt der Mittellinie, falls vorhanden
    if centerline and len(centerline) > 1:
        start_x, start_y = centerline[0]
        end_x, end_y = centerline[-1]
        
        # Startpunkt: blauer halbtransparenter Kreis
        plt.scatter(start_x, start_y, s=150, color='blue', alpha=0.6, marker='o', zorder=5, label='Start')
        
        # Endpunkt: grüne halbtransparente Raute (Diamond)
        plt.scatter(end_x, end_y, s=150, color='green', alpha=0.6, marker='D', zorder=5, label='Ende')

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

    # Ausgabe der Eingabedaten neben dem Plot
    # Erstelle eine Textbox für die Eingabedaten
    # Die Positionierung erfolgt relativ zur Figure (0,0 links unten, 1,1 rechts oben)
    # Wir platzieren sie rechts neben dem Plot.

    # Sammle die relevanten Konfigurationsparameter
    config_text = "Konfiguration:\n"
    config_text += f"  Track-Breite: {config.get('track_width')}\n"
    config_text += f"  Glättungsfenster: {config.get('smoothing_window')}\n"

    # Einfacher Ansatz: Zeige die wichtigsten Parameter, die immer gelten
    # oder die für die aktuelle Visualisierung relevant sein könnten.
    # Basisparameter für alle Modi
    param_summary = {
        "Track Breite": config.get('track_width'),
        "Glättung": config.get('smoothing_window'),
        "Max. Schließfaktor": config.get('max_closing_length_factor'),
        "Punkte (Mitte)": len(centerline) if centerline else 0,
    }
    
    # Aktiver Mode-String ermitteln
    mode_nummern = {0: "Random Track", 1: "Script Track", 2: "CSV Track", 
                    3: "Fixed Polar", 4: "Random Polar+Arc"}
    aktiver_modus = "Unbekannt"
    for mode_num, mode_name in mode_nummern.items():
        if config.get('default_run_mode') == mode_num:
            aktiver_modus = f"{mode_num} ({mode_name})"
    
    # Mode 4 (Polar Track) Parameter, die wichtig für die Diagnose sind
    param_summary["Aktiver Modus"] = aktiver_modus
    param_summary["Num Points Polar"] = config.get('num_points_polar_random')
    param_summary["Polar Distanz Bereich"] = config.get('polar_distance_range_random')
    param_summary["Kurventypen"] = config.get('curve_types_polar_random')
    param_summary["Arc Radius Min/Max"] = [config.get('polar_arc_radius_min'), config.get('polar_arc_radius_max')]
    param_summary["Arc Max Winkel"] = config.get('polar_arc_max_angle_deg')
    param_summary["Arc Punkte"] = config.get('polar_arc_num_points')
    param_summary["Geschlossener Track"] = config.get('create_closed_track_default', True)
    
    text_to_display = "Eingabeparameter (Auszug):\n"
    for key, value in param_summary.items():
        text_to_display += f"  {key}: {value}\n"

    # Aktiver Mode
    mode_nummern = {0: "Random Track", 1: "Script Track", 2: "CSV Track", 
                    3: "Fixed Polar", 4: "Random Polar+Arc"}
    active_mode = config.get('default_run_mode', 0)
    text_to_display += f"\nAktiver Modus: {active_mode} ({mode_nummern.get(active_mode, 'Unbekannt')})\n"
    text_to_display += f"Geschlossener Track: {config.get('create_closed_track_default', True)}"
    
    # Position der Textbox anpassen
    # Versuche, die Textbox rechts vom Plot zu platzieren.
    # Dafür muss der rechte Rand des Subplots angepasst werden.
    fig.subplots_adjust(right=0.75) # Schafft Platz auf der rechten Seite
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    fig.text(0.77, 0.95, text_to_display, transform=fig.transFigure, fontsize=10,
             verticalalignment='top', bbox=props)

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

# Entferne die alten print-Anweisungen, da die Konfiguration jetzt zentralisiert ist
# print("trackgenlib.py wurde initialisiert und Konfiguration geladen.")
# print(f"Konfiguration: track_width={config.get('track_width')}, script_example='{config.get('script_path_example')}', csv_example='{config.get('csv_path_example')}'")

def close_track_smoothly(track_points):
    """Schließt einen Track glatt, ohne zu große Segmente zum Startpunkt zu erzeugen.
    Sorgt dafür, dass die Steigung am Anfang und Ende des Tracks gleich ist.
    
    Args:
        track_points: Liste von (x, y) Koordinaten des Tracks
        
    Returns:
        Die ergänzte Liste von Punkten mit glatter Schließung zum Startpunkt
    """
    if not track_points or len(track_points) < 2:
        return track_points
        
    # Wenn der Track bereits geschlossen ist, nichts zu tun
    if track_points[0] == track_points[-1]:
        return track_points
        
    # Berechne die durchschnittliche Segmentlänge
    total_length = 0.0
    segment_lengths = []
    for i in range(1, len(track_points)):
        dx = track_points[i][0] - track_points[i-1][0]
        dy = track_points[i][1] - track_points[i-1][1]
        segment_length = np.sqrt(dx**2 + dy**2)
        segment_lengths.append(segment_length)
        total_length += segment_length
        
    avg_segment_length = total_length / len(segment_lengths) if segment_lengths else 1.0
    
    # Berechne die Distanz zwischen dem letzten und dem ersten Punkt
    first_point = track_points[0]
    last_point = track_points[-1]
    dx_closing = first_point[0] - last_point[0]
    dy_closing = first_point[1] - last_point[1]
    closing_distance = np.sqrt(dx_closing**2 + dy_closing**2)
    
    # Berechne die Steigungen am Anfang und Ende des Tracks
    # Für Anfangssteigung: Vektor vom ersten zum zweiten Punkt
    if len(track_points) > 1:
        start_slope_x = track_points[1][0] - track_points[0][0]
        start_slope_y = track_points[1][1] - track_points[0][1]
        start_angle = math.atan2(start_slope_y, start_slope_x)
    else:
        start_angle = 0
    
    # Für Endsteigung: Vektor vom vorletzten zum letzten Punkt
    if len(track_points) > 1:
        end_slope_x = track_points[-1][0] - track_points[-2][0]
        end_slope_y = track_points[-1][1] - track_points[-2][1]
        end_angle = math.atan2(end_slope_y, end_slope_x)
    else:
        end_angle = 0
    
    # Wenn die Schließungsdistanz zu groß ist, füge zusätzliche Punkte hinzu
    max_closing_length = avg_segment_length * config.get('max_closing_length_factor', 1.5)
    
    if closing_distance > max_closing_length:
        # Berechne Winkel zwischen Start und Ende
        angle_diff = (start_angle - end_angle) % (2 * math.pi)
        if angle_diff > math.pi:
            angle_diff -= 2 * math.pi  # Normalisiere auf [-π, π]
        
        # Bei großem Winkelunterschied: Erzeuge einen Kreisbogen statt linearer Interpolation
        if abs(angle_diff) > math.radians(30):
            # Berechne einen geeigneten Radius für den Bogen
            # basierend auf der Distanz und dem Winkelunterschied
            arc_radius = closing_distance / (2 * math.sin(abs(angle_diff)/2)) if abs(angle_diff) > 0.001 else closing_distance * 2
            
            # Berechne Mittelpunkt des Kreisbogens
            # Der Bogen sollte an beiden Enden tangential zu den Steigungen sein
            # Wir platzieren den Mittelpunkt senkrecht zur mittleren Richtung
            avg_angle = (end_angle + start_angle) / 2
            perp_angle = avg_angle + math.pi/2 * (1 if angle_diff > 0 else -1)
            
            # Mittelpunkt berechnen
            center_x = (first_point[0] + last_point[0]) / 2 + arc_radius * math.cos(perp_angle)
            center_y = (first_point[1] + last_point[1]) / 2 + arc_radius * math.sin(perp_angle)
            
            # Winkel vom Mittelpunkt zum letzten Punkt
            angle_to_last = math.atan2(last_point[1] - center_y, last_point[0] - center_x)
            angle_to_first = math.atan2(first_point[1] - center_y, first_point[0] - center_x)
            
            # Winkel zwischen diesen beiden Punkten
            arc_angle = (angle_to_first - angle_to_last) % (2 * math.pi)
            if arc_angle > math.pi:
                arc_angle -= 2 * math.pi  # Normalisiere auf [-π, π]
            
            # Erzeuge Bogenpunkte
            num_points = max(3, int(abs(arc_angle) / math.radians(15)))  # Ca. alle 15 Grad ein Punkt
            for i in range(1, num_points):
                fraction = i / num_points
                current_angle = angle_to_last + fraction * arc_angle
                x = center_x + arc_radius * math.cos(current_angle)
                y = center_y + arc_radius * math.sin(current_angle)
                track_points.append((x, y))
        else:
            # Bei kleinem Winkelunterschied: Lineare Interpolation
            num_points = int(np.ceil(closing_distance / avg_segment_length))
            for i in range(1, num_points):
                # Lineare Interpolation zwischen letztem und erstem Punkt
                fraction = i / num_points
                x = last_point[0] + fraction * dx_closing
                y = last_point[1] + fraction * dy_closing
                track_points.append((x, y))
    
    # Schließlich füge den ersten Punkt hinzu, um den Track zu schließen
    track_points.append(first_point)
    
    return track_points
