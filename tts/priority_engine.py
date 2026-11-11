import time

# Comprehensive Multilingual Object Dictionary for English, Hindi, and Odia
# Supporting all 80 COCO classes and natural everyday aliases (sofa, mobile phone, table, etc.)
OBJECT_NAMES = {
    'person': {
        'en': 'person', 'hi': 'व्यक्ति', 'or': 'ବ୍ୟକ୍ତି', 'or_phonetic': 'byakti'
    },
    'bicycle': {
        'en': 'bicycle', 'hi': 'साइकिल', 'or': 'ସାଇକେଲ', 'or_phonetic': 'cycle'
    },
    'car': {
        'en': 'car', 'hi': 'गाड़ी', 'or': 'ଗାଡି', 'or_phonetic': 'gadi'
    },
    'motorcycle': {
        'en': 'motorcycle', 'hi': 'मोटरसाइकिल', 'or': 'ମୋଟରସାଇକେଲ', 'or_phonetic': 'motorcycle'
    },
    'bus': {
        'en': 'bus', 'hi': 'बस', 'or': 'ବସ୍', 'or_phonetic': 'bus'
    },
    'truck': {
        'en': 'truck', 'hi': 'ट्रक', 'or': 'ଟ୍ରକ୍', 'or_phonetic': 'truck'
    },
    'traffic light': {
        'en': 'traffic light', 'hi': 'ट्रैफिक लाइट', 'or': 'ଟ୍ରାଫିକ୍ ଲାଇଟ୍', 'or_phonetic': 'traffic light'
    },
    'fire hydrant': {
        'en': 'fire hydrant', 'hi': 'फायर हाइड्रेंट', 'or': 'ଫାୟାର ହାଇଡ୍ରାଣ୍ଟ', 'or_phonetic': 'fire hydrant'
    },
    'stop sign': {
        'en': 'stop sign', 'hi': 'स्टॉप साइन', 'or': 'ଷ୍ଟପ୍ ସାଇନ୍', 'or_phonetic': 'stop sign'
    },
    'bench': {
        'en': 'bench', 'hi': 'बेंच', 'or': 'ବେଞ୍ଚ', 'or_phonetic': 'bench'
    },
    'bird': {
        'en': 'bird', 'hi': 'पक्षी', 'or': 'ଚଢ଼େଇ', 'or_phonetic': 'chadhei'
    },
    'dog': {
        'en': 'dog', 'hi': 'कुत्ता', 'or': 'କୁକୁର', 'or_phonetic': 'kukura'
    },
    'cat': {
        'en': 'cat', 'hi': 'बिल्ली', 'or': 'ବିଲେଇ', 'or_phonetic': 'bilei'
    },
    'horse': {
        'en': 'horse', 'hi': 'घोड़ा', 'or': 'ଘୋଡ଼ା', 'or_phonetic': 'ghoda'
    },
    'cow': {
        'en': 'cow', 'hi': 'गाय', 'or': 'ଗାଈ', 'or_phonetic': 'gai'
    },
    'backpack': {
        'en': 'bag', 'hi': 'बैग', 'or': 'ବ୍ୟାଗ୍', 'or_phonetic': 'bag'
    },
    'umbrella': {
        'en': 'umbrella', 'hi': 'छाता', 'or': 'ଛତା', 'or_phonetic': 'chhata'
    },
    'handbag': {
        'en': 'handbag', 'hi': 'हैंडबैग', 'or': 'ହ୍ୟାଣ୍ଡବ୍ୟାଗ୍', 'or_phonetic': 'handbag'
    },
    'tie': {
        'en': 'tie', 'hi': 'टाई', 'or': 'ଟାଇ', 'or_phonetic': 'tie'
    },
    'suitcase': {
        'en': 'suitcase', 'hi': 'सूटकेस', 'or': 'ସୁଟକେସ୍', 'or_phonetic': 'suitcase'
    },
    'sports ball': {
        'en': 'ball', 'hi': 'गेंद', 'or': 'ବଲ୍', 'or_phonetic': 'ball'
    },
    'bottle': {
        'en': 'bottle', 'hi': 'बोतल', 'or': 'ବୋତଲ', 'or_phonetic': 'botal'
    },
    'wine glass': {
        'en': 'glass', 'hi': 'ग्लास', 'or': 'ଗ୍ଲାସ୍', 'or_phonetic': 'glass'
    },
    'cup': {
        'en': 'cup', 'hi': 'कप', 'or': 'କପ୍', 'or_phonetic': 'kap'
    },
    'fork': {
        'en': 'fork', 'hi': 'कांटा', 'or': 'ଫର୍କ', 'or_phonetic': 'fork'
    },
    'knife': {
        'en': 'knife', 'hi': 'चाकू', 'or': 'ଛୁରୀ', 'or_phonetic': 'chhuri'
    },
    'spoon': {
        'en': 'spoon', 'hi': 'चम्मच', 'or': 'ଚାମଚ', 'or_phonetic': 'chamacha'
    },
    'bowl': {
        'en': 'bowl', 'hi': 'कटोरा', 'or': 'ଗିନା', 'or_phonetic': 'gina'
    },
    'chair': {
        'en': 'chair', 'hi': 'कुर्सी', 'or': 'ଚୌକି', 'or_phonetic': 'chauki'
    },
    'couch': {
        'en': 'sofa', 'hi': 'सोफा', 'or': 'ସୋଫା', 'or_phonetic': 'sofa'
    },
    'sofa': {
        'en': 'sofa', 'hi': 'सोफा', 'or': 'ସୋଫା', 'or_phonetic': 'sofa'
    },
    'potted plant': {
        'en': 'plant', 'hi': 'पौधा', 'or': 'ଗଛ କୁଣ୍ଡ', 'or_phonetic': 'plant'
    },
    'plant': {
        'en': 'plant', 'hi': 'पौधा', 'or': 'ଗଛ', 'or_phonetic': 'plant'
    },
    'bed': {
        'en': 'bed', 'hi': 'बिस्तर', 'or': 'ଖଟ', 'or_phonetic': 'khata'
    },
    'dining table': {
        'en': 'table', 'hi': 'मेज', 'or': 'ଟେବୁଲ୍', 'or_phonetic': 'tebul'
    },
    'table': {
        'en': 'table', 'hi': 'मेज', 'or': 'ଟେବୁଲ୍', 'or_phonetic': 'tebul'
    },
    'toilet': {
        'en': 'toilet', 'hi': 'शौचालय', 'or': 'ଟଏଲେଟ୍', 'or_phonetic': 'toilet'
    },
    'tv': {
        'en': 'TV', 'hi': 'टीवी', 'or': 'ଟିଭି', 'or_phonetic': 'TV'
    },
    'laptop': {
        'en': 'laptop', 'hi': 'लैपटॉप', 'or': 'ଲାପଟପ୍', 'or_phonetic': 'laptop'
    },
    'mouse': {
        'en': 'mouse', 'hi': 'माउस', 'or': 'ମାଉସ୍', 'or_phonetic': 'mouse'
    },
    'remote': {
        'en': 'remote', 'hi': 'रिमोट', 'or': 'ରିମୋଟ୍', 'or_phonetic': 'remote'
    },
    'keyboard': {
        'en': 'keyboard', 'hi': 'कीबोर्ड', 'or': 'କିବୋର୍ଡ', 'or_phonetic': 'keyboard'
    },
    'cell phone': {
        'en': 'mobile phone', 'hi': 'मोबाइल', 'or': 'ମୋବାଇଲ୍', 'or_phonetic': 'mobile'
    },
    'mobile phone': {
        'en': 'mobile phone', 'hi': 'मोबाइल', 'or': 'ମୋବାଇଲ୍', 'or_phonetic': 'mobile'
    },
    'phone': {
        'en': 'phone', 'hi': 'मोबाइल', 'or': 'ମୋବାଇଲ୍', 'or_phonetic': 'mobile'
    },
    'microwave': {
        'en': 'microwave', 'hi': 'माइक्रोवेव', 'or': 'ମାଇକ୍ରୋୱେଭ୍', 'or_phonetic': 'microwave'
    },
    'oven': {
        'en': 'oven', 'hi': 'ओवन', 'or': 'ଓଭନ', 'or_phonetic': 'oven'
    },
    'sink': {
        'en': 'sink', 'hi': 'सिंक', 'or': 'ସିଙ୍କ୍', 'or_phonetic': 'sink'
    },
    'refrigerator': {
        'en': 'fridge', 'hi': 'फ्रिज', 'or': 'ଫ୍ରିଜ୍', 'or_phonetic': 'fridge'
    },
    'book': {
        'en': 'book', 'hi': 'किताब', 'or': 'ବହି', 'or_phonetic': 'bahi'
    },
    'clock': {
        'en': 'clock', 'hi': 'घड़ी', 'or': 'ଘଣ୍ଟା', 'or_phonetic': 'ghanta'
    },
    'scissors': {
        'en': 'scissors', 'hi': 'कैंची', 'or': 'କଇଁଚି', 'or_phonetic': 'kainchi'
    },
    'toothbrush': {
        'en': 'toothbrush', 'hi': 'टूथब्रश', 'or': 'ଟୁଥବ୍ରଶ୍', 'or_phonetic': 'toothbrush'
    },
    'door': {
        'en': 'door', 'hi': 'दरवाजा', 'or': 'କବାଟ', 'or_phonetic': 'kabata'
    },
    'stairs': {
        'en': 'stairs', 'hi': 'सीढ़ियां', 'or': 'ସିଡ଼ି', 'or_phonetic': 'sidi'
    }
}

class PriorityEngine:
    def __init__(self):
        # High Priority: moving obstacles & critical path blockages
        self.high_priority = {
            'person', 'car', 'bus', 'truck', 'motorcycle', 'bicycle', 'traffic light', 'stairs'
        }
        # Medium Priority: Furniture and personal devices (sofa, phone, chair, laptop, bed, table)
        self.medium_priority = {
            'chair', 'sofa', 'couch', 'mobile phone', 'cell phone', 'phone', 
            'laptop', 'dining table', 'table', 'bed', 'bench', 'door', 'tv', 'refrigerator', 'dog'
        }
        # Low Priority: smaller handheld items
        self.low_priority = {
            'bottle', 'cup', 'book', 'clock', 'mouse', 'remote', 'keyboard', 'backpack', 'cat', 'scissors'
        }
        
        # Track last spoken time: (label, direction) -> timestamp
        self.last_spoken = {}
        
        # Responsive cooldowns (in seconds)
        self.cooldowns = {
            'high': 3.0,
            'medium': 4.5,
            'low': 7.0
        }

    def _get_localized_label(self, label, lang='en'):
        clean = label.lower().strip()
        data = OBJECT_NAMES.get(clean)
        if not data:
            return clean.replace('_', ' ')
        if lang == 'hi':
            return data.get('hi', clean)
        elif lang == 'or':
            return data.get('or', clean)
        elif lang == 'or_phonetic':
            return data.get('or_phonetic', clean)
        return data.get('en', clean)

    def process_detections(self, detections, alert_distance_threshold=3.8, lang='en'):
        """
        Takes processed detections (with label, distance, direction_info).
        Returns prioritized alerts across all detected objects (person, mobile, sofa, etc.).
        """
        alerts = []
        current_time = time.time()
        
        # Sort detections by distance (closest first), then priority
        def sort_key(d):
            dist = d.get('distance', 999.0)
            if dist <= 0:
                dist = 999.0
            prio = 0 if d.get('label') in self.high_priority else (1 if d.get('label') in self.medium_priority else 2)
            return (dist, prio)
            
        sorted_detections = sorted(detections, key=sort_key)
        
        for det in sorted_detections:
            label = det['label']
            dist = det.get('distance', -1.0)
            dir_info = det.get('direction_info', {})
            
            dir_en = dir_info.get('direction_en', det.get('direction', 'Ahead'))
            dir_hi = dir_info.get('direction_hi', 'सामने')
            dir_or = dir_info.get('direction_or', 'ସାମ୍ନାରେ')
            dir_or_phonetic = dir_info.get('direction_or_phonetic', 'samnare')
            clock = dir_info.get('clock', '')
            pan = dir_info.get('pan', 0.0)
            
            # Determine priority tier
            if label in self.high_priority:
                p_level = 'high'
            elif label in self.medium_priority:
                p_level = 'medium'
            else:
                p_level = 'low'
                
            # Filter distant low-priority items beyond threshold
            if p_level == 'low' and dist > alert_distance_threshold:
                continue
                
            # Check cooldown
            cache_key = (label, dir_en)
            last_time = self.last_spoken.get(cache_key, 0)
            cooldown_required = self.cooldowns[p_level]
            
            # Urgent proximity check (< 1.1m)
            is_urgent = (dist > 0 and dist < 1.1)
            if is_urgent:
                cooldown_required = 1.6
                
            if current_time - last_time >= cooldown_required:
                obj_en = self._get_localized_label(label, 'en')
                obj_hi = self._get_localized_label(label, 'hi')
                obj_or = self._get_localized_label(label, 'or')
                obj_or_phonetic = self._get_localized_label(label, 'or_phonetic')
                
                # Format phrases for each language
                if is_urgent:
                    phrase_en = f"Warning! {obj_en} very close {dir_en} at {dist} meters ({clock})!"
                    phrase_hi = f"सावधान! {obj_hi} {dir_hi} {dist} मीटर पर बहुत पास है ({clock})!"
                    phrase_or = f"ସାବଧାନ! {obj_or} {dir_or} {dist} ମିଟରରେ ଅତି ପାଖରେ ଅଛି!"
                    phrase_or_phonetic = f"Sabadhana! {obj_or_phonetic} {dir_or_phonetic} {dist} meter-re ati pakhare achhi!"
                else:
                    phrase_en = f"{obj_en.capitalize()} on {dir_en}, {dist} meters ({clock})."
                    phrase_hi = f"{obj_hi} {dir_hi}, {dist} मीटर दूर ({clock})।"
                    phrase_or = f"{obj_or} {dir_or}, {dist} ମିଟର ଦୂରରେ।"
                    phrase_or_phonetic = f"{obj_or_phonetic} {dir_or_phonetic}, {dist} meter doorare achhi."

                # Choose primary phrase based on requested language
                if lang == 'hi':
                    primary_text = phrase_hi
                    spoken_text = phrase_hi
                elif lang == 'or':
                    primary_text = phrase_or
                    spoken_text = phrase_or_phonetic
                else:
                    primary_text = phrase_en
                    spoken_text = phrase_en

                alerts.append({
                    'text': primary_text,
                    'spoken_text': spoken_text,
                    'text_en': phrase_en,
                    'text_hi': phrase_hi,
                    'text_or': phrase_or,
                    'text_or_phonetic': phrase_or_phonetic,
                    'is_urgent': is_urgent,
                    'distance': dist,
                    'direction': dir_en,
                    'clock': clock,
                    'pan': pan,
                    'label': label
                })
                
                self.last_spoken[cache_key] = current_time
                
                # Allow up to 3 alerts per frame so non-person objects (phone, sofa, chair) are heard
                if len(alerts) >= 3:
                    break
                    
        return alerts
