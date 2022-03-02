import pynput
from pynput import keyboard
import string
import pickle
import pyperclip
import pygtrie
import os
import sys

# On OSX, ability to detect alphanumeric key presses just stopped working at one point,
# possibly because of a software update. The permissions in 'Security &
# Privacy'->Accessibility->Privacy had to be reset by manually using '+' key, finding the
# standalone app, and adding the app.
# Need to handle capitalization and preserve capitalization
# Experimenting with key chords: Problem is that holding an alphanumeric key down
# triggers 'repeats'. Alphanumerics are propagated to the OS. Might be interesting
# to see if suppressing specific events (described in the pynput FAQ) might be of use

CTRL_KEYS = {keyboard.Key.ctrl_r, keyboard.Key.cmd}
COMPLETION_HOTKEY = {keyboard.Key.ctrl_r, keyboard.Key.cmd, keyboard.KeyCode.from_char ('z')}
ADD_HOTKEY = {keyboard.Key.ctrl_r, keyboard.Key.cmd, keyboard.KeyCode.from_char (';')}
SAVE_HOTKEY = {keyboard.Key.ctrl_r, keyboard.Key.cmd, keyboard.KeyCode.from_char ('=')}

WHITE_SPACE = {keyboard.Key.space, keyboard.Key.enter, keyboard.Key.tab}
DELETE = {keyboard.Key.backspace}
CTRL = {keyboard.Key.ctrl_r}
ARROWS = {keyboard.Key.left, keyboard.Key.right, keyboard.Key.up, keyboard.Key.down}

trie_name = sys.argv[1]

class Completable:
    # A string of potentially completable characters
    def __init__ (self):
        self.cur_word = ""
        self.active_index = 0
        self.full_word = ""
        self.last_insert_len = 0

    def try_saving (self):
        # save contents of current trie to file
        print ('Save hotkey.')
        os.remove(trie_name)
        pickle.dump(newt, open(trie_name, "wb"), protocol=pickle.HIGHEST_PROTOCOL)

    def try_adding_word (self):
        # add contents of clipboard to trie. Probably should
        # add choice of persist or not, and have mechanism
        # for when that occurs. Currently it's done via hotkey only
        print ('Add hotkey.')
        word_to_add = pyperclip.paste()
        print ('Word to add is ', word_to_add)
        newt[word_to_add] = True

    def is_none (self, key):
        return (key.char is None)

    def handle_delete (self):
        self.cur_word = self.cur_word[:-1]
        print ("After DELETE, cur_word now ", self.cur_word)

    def handle_whitespace (self):
        print ("WHITE_SPACE detected, now no current word")
        self.cur_word = ""
        self.full_word = ""
        self.last_insert_len = 0
        print ("end of word")

    def handle_alphanumeric (self, key):
        try:
            print('alphanumeric key {0} pressed'.format(key.char))
            if not keyboard_state.was_ctrl_x(key) and \
               not keyboard_state.any_modifiers_active ():
                self.cur_word += key.char
                print ("cur_word updated to ", self.cur_word)
                self.active_index = 0
        except AttributeError:
            pass
        
    def try_to_complete (self, key):
        print('Completion hotkey with cur_word ', self.cur_word)
        if (len(self.cur_word) > 1): 
            try:
                # Only complete if the last character entered was alphanumeric
                if (hasattr (keyboard_state.last_keys[-1], 'char')):
                    completion_list = newt.items(prefix=self.cur_word)
                    print ("completion_list is ", completion_list, len(completion_list))
                    print ('current word is ', self.cur_word)
                    if (self.active_index >= len(completion_list)):
                        self.active_index = 0
                    print('active_index is ', self.active_index)
                    com_word = completion_list[self.active_index][0]
                    print ("com_word is ", com_word)
                    l = len (self.cur_word)
                    completion = com_word[l:]
                    for i in range (self.last_insert_len):
                        kcontroller.press(keyboard.Key.backspace)
                    kcontroller.type(completion)
                    self.last_insert_len = len(completion)
                    # cur_word = ""
                    self.full_word = self.cur_word + completion
                    self.active_index += 1
                else:
                    # something like an up arrow or something other than
                    # an alphanumeric was the key used right before
                    # completion was invoked, so don't do a completion
                    print ("Now there is no current word for completion")
                    self.cur_word = ""
                    self.full_word = ""
                    self.last_insert_len = 0
                    self.active_index = 0
            except KeyError:
                print ('completion KeyError')
                self.active_index = 0
                pass
            except AttributeError:
                print ('completion AttributeError')
                self.active_index = 0
                pass
            except IndexError:
                print ('completion IndexError')
                self.active_index = 0
                pass

class KeyboardState:
    def __init__ (self):
        self.modifiers_active = False
        self.last_keys = []
        self.cur_keys  = set()
        
    def was_ctrl_x (self, key):
    # Was previous key sequence Ctrl-x?
        try:
            if (self.last_keys[-1] == keyboard.Key.ctrl_r) and \
               (self.last_keys[-2].char == 'x'):
                print ("was control Xed")
                return True
            else:
                return False
        except IndexError:
            return False

    def any_modifiers_active (self):
        # Are any modifier keys down at all?
        for k in self.cur_keys:
            if k in CTRL_KEYS:
                return True
        return False    
    
    def is_completion_hotkey (self, key):
        if key in COMPLETION_HOTKEY:
            self.cur_keys.add(key)
            if all (k in self.cur_keys for k in COMPLETION_HOTKEY):
                return True
        return False

    def is_save_hotkey (self, key):
        if key in SAVE_HOTKEY:
            self.cur_keys.add(key)
            if all (k in self.cur_keys for k in SAVE_HOTKEY):
                return True
        return False

    def is_add_hotkey (self, key):
        if key in ADD_HOTKEY:
            self.cur_keys.add(key)
            if all (k in self.cur_keys for k in ADD_HOTKEY):
                return True
        return False

    def on_press(self, key):
        if self.is_completion_hotkey (key):
            completable.try_to_complete (key)
        elif self.is_add_hotkey (key):
            completable.try_adding_word()
        elif self.is_save_hotkey (key):
            completable.try_saving()
        else:
            # we don't do anything with characters based
            # on on_press, we do it with on_release
            pass
        

    def on_release (self, key):
        # Detecting keys on their release is important in that
        # injected keys from this app won't generate on release events
        
        print('{0} released'.format(key))

        if key == keyboard.Key.esc:
            # Stop listener
            return False

        if key in WHITE_SPACE:
            completable.handle_whitespace()
            
        if key in DELETE:
            completable.handle_delete()
            
        if (hasattr (key, 'char')):
            if (key.char is not None): completable.handle_alphanumeric(key)
        else:
            # presumably this is something like an arrow key
            # which moved the cursor away from a completion candidate
            completable.handle_whitespace()
            
        # Update the state of the keyboard
        try:
            self.last_keys.append(key)
            self.cur_keys.remove(key)
        except KeyError:
            pass

        
newt = pickle.load (open (trie_name, "rb"))

kcontroller = keyboard.Controller ()

completable = Completable ()
keyboard_state = KeyboardState ()

listener = keyboard.Listener (on_press   = keyboard_state.on_press,
                              on_release = keyboard_state.on_release)

listener.start()
listener.join()



