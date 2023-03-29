class TextFinder():
    def __init__(self):
        pass

    def find_text(self, s, text):
        '''
        Finds the first occurence of text in s and returns the index
        '''
        positions = []
        best_guess = None
        signature_len = 16
        
        while signature_len >= 1 and signature_len <= len(s):
            signature = self._gen_signature(s)
            print(signature)
            matching_positions = self._search_signature(signature, text)

            # simple case: only one match
            if len(matching_positions) == 1:
                return matching_positions[0]
            
            # If there are no matches, reduce the signature length
            elif len(matching_positions) == 0:
                # if there is a best guess, return it
                if best_guess:
                    return best_guess

                signature_len -= 1
                continue

            # If there are multiple matches...
            # Store the first match as best guess, increase the signature length and continue
            else:
                best_guess = matching_positions[0]
                signature_len += 1
                continue
    
    def _gen_signature(self, s, signature_length = 16):
        signature = ''
        for char in s:
            if char.isalnum():
                signature += char.lower()
            
            if len(signature) >= signature_length:
                break
        return signature
    
    def _search_signature(self, signature, text):
        '''
        Searches for the signature in the text
        '''
        positions = []
        for i in range(len(text)):
            
            # Igoree non-alphanumeric characters
            if not text[i].isalnum():
                continue

            pos_signature = self._gen_signature(text[i:], len(signature))
            if pos_signature == signature:
                positions.append(i)

        return positions

class ApproximateMap():
    def __init__(self, inital_values = None):
        self.values = []
        # Initial values should be a list of tuples
        if inital_values:
            for value in inital_values:
                self.add(value)
    
    def add(self, key, value):
        '''
        Adds a value to the map
        '''

        self.values.append((key, value))
        self.values.sort(key=lambda x: x[0])
    
    def get_lt(self, key):
        '''
        Returns the greatest value that is less than key
        '''
        for value in reversed(self.values):
            if value[0] < key:
                return value
    
    def get_gt(self, key):
        '''
        Returns the least value that is greater than key
        '''
        for value in self.values:
            if value[0] > key:
                return value
    
    def get_lteq(self, key):
        '''
        Returns the greatest value that is less than or equal to key
        '''
        for value in reversed(self.values):
            if value[0] <= key:
                return value
    
    def get_gteq(self, key):
        '''
        Returns the least value that is greater than or equal to key
        '''
        for value in self.values:
            if value[0] >= key:
                return value