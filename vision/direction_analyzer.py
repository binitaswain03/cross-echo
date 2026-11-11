"""
Direction and Angle Analyzer for CrossEcho Spatial Navigation
Calculates granular horizontal angles, clock positions, and multilingual directions
(English, Hindi, Odia) for visually impaired orientation and mobility.
"""

import math

class DirectionAnalyzer:
    def __init__(self, horizontal_fov=65.0):
        """
        horizontal_fov: Camera horizontal Field of View in degrees (default 65° for standard webcams).
        """
        self.hfov = horizontal_fov
        
        # Multilingual direction labels
        self.direction_translations = {
            'Far Left': {
                'en': 'Far Left',
                'hi': 'बहुत बाईं तरफ',
                'or': 'ଅତି ବାମ ପଟେ',
                'or_phonetic': 'Ati bama pate'
            },
            'Left': {
                'en': 'Left',
                'hi': 'बाईं तरफ',
                'or': 'ବାମ ପଟେ',
                'or_phonetic': 'Bama pate'
            },
            'Slight Left': {
                'en': 'Slight Left',
                'hi': 'थोड़ा बाईं तरफ',
                'or': 'ଟିକେ ବାମ ପଟେ',
                'or_phonetic': 'Tike bama pate'
            },
            'Ahead': {
                'en': 'Straight Ahead',
                'hi': 'बिल्कुल सामने',
                'or': 'ସାମ୍ନାରେ',
                'or_phonetic': 'Samnare'
            },
            'Slight Right': {
                'en': 'Slight Right',
                'hi': 'थोड़ा दाईं तरफ',
                'or': 'ଟିକେ ଡାହାଣ ପଟେ',
                'or_phonetic': 'Tike dahana pate'
            },
            'Right': {
                'en': 'Right',
                'hi': 'दाईं तरफ',
                'or': 'ଡାହାଣ ପଟେ',
                'or_phonetic': 'Dahana pate'
            },
            'Far Right': {
                'en': 'Far Right',
                'hi': 'बहुत दाईं तरफ',
                'or': 'ଅତି ଡାହାଣ ପଟେ',
                'or_phonetic': 'Ati dahana pate'
            }
        }

    def analyze(self, frame_width, box):
        """
        Analyzes horizontal angle and position for a bounding box [x1, y1, x2, y2].
        Returns a rich direction dictionary with angle in degrees, clock position,
        and localized direction strings.
        """
        x1, y1, x2, y2 = box
        center_x = (x1 + x2) / 2.0
        
        # Normalized horizontal offset: -1.0 (far left) to +1.0 (far right)
        half_w = frame_width / 2.0
        if half_w <= 0:
            half_w = 320.0
        norm_x = (center_x - half_w) / half_w
        norm_x = max(-1.0, min(1.0, norm_x))
        
        # Calculate real angular displacement from camera optical center (in degrees)
        angle_deg = round(norm_x * (self.hfov / 2.0), 1)
        
        # High-precision directional categorization
        if norm_x < -0.60:
            dir_key = 'Far Left'
            clock = '9 o\'clock' if norm_x < -0.80 else '10 o\'clock'
        elif norm_x < -0.22:
            dir_key = 'Left'
            clock = '10 o\'clock'
        elif norm_x < -0.07:
            dir_key = 'Slight Left'
            clock = '11 o\'clock'
        elif norm_x <= 0.07:
            dir_key = 'Ahead'
            clock = '12 o\'clock'
        elif norm_x <= 0.22:
            dir_key = 'Slight Right'
            clock = '1 o\'clock'
        elif norm_x <= 0.60:
            dir_key = 'Right'
            clock = '2 o\'clock'
        else:
            dir_key = 'Far Right'
            clock = '3 o\'clock' if norm_x > 0.80 else '2 o\'clock'

        # Panning value for Web Audio binaural stereo sound (-1.0 to +1.0)
        pan = round(norm_x, 2)
        
        trans = self.direction_translations.get(dir_key, self.direction_translations['Ahead'])
        
        return {
            'direction': dir_key,
            'direction_en': trans['en'],
            'direction_hi': trans['hi'],
            'direction_or': trans['or'],
            'direction_or_phonetic': trans['or_phonetic'],
            'angle': angle_deg,
            'angle_str': f"{abs(angle_deg)}° {'Left' if angle_deg < 0 else ('Right' if angle_deg > 0 else 'Center')}",
            'clock': clock,
            'pan': pan
        }
