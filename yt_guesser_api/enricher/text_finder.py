class TextFinder():
    def __init__():
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
            pos_signature = self._gen_signature(text[i:], len(signature))
            if pos_signature == signature:
                positions.append(i)

        return positions