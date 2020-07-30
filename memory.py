import math

import numpy as np
from random import randrange


MEMORY_SIZE = 1024


class OldBlock:
    data = 0
    address = 0
    was_dirty = False


class MemorySettings:
    num_sets = 1
    num_blocks_per_set = 1
    num_words_per_block = 1
    cache_active = False
    cache_replacement_policy = "random"
    cache_is_write_back = True

    memory_wait_cycles = 0


class Cache:
    def __init__(self, sets=1, blocks_per_set=1, words_per_block=1):
        self.contents = np.zeros((sets, blocks_per_set, words_per_block), dtype=np.int)
        self.tags = np.zeros((sets, blocks_per_set), dtype=np.int)
        self.valid_bits = np.zeros((sets, blocks_per_set), dtype=np.int)
        self.dirty_bits = np.zeros((sets, blocks_per_set), dtype=np.int)
        self.size = {"sets": sets, "blocks_per_set": blocks_per_set, "words_per_block": words_per_block}
        self.book_keeping_was_modified = False
        self.book_keeping_modified_words = []
        self.book_keeping_modified_block = False
        self.book_keeping_modified_set = 0

    def resize(self, sets=1, blocks_per_set=1, words_per_block=1):
        self.contents = np.zeros((sets, blocks_per_set, words_per_block), dtype=np.int)
        self.tags = np.zeros((sets, blocks_per_set), dtype=np.int)
        self.valid_bits = np.zeros((sets, blocks_per_set), dtype=np.int)
        self.dirty_bits = np.zeros((sets, blocks_per_set), dtype=np.int)
        MemorySettings.num_sets = sets
        MemorySettings.num_blocks_per_set = blocks_per_set
        MemorySettings.num_words_per_block = words_per_block
        self.size = {"sets": sets, "blocks_per_set": blocks_per_set, "words_per_block": words_per_block}

    def modify(self, address, data, word_index):
        tag = (address >> int(math.log2(MemorySettings.num_words_per_block)))
        set = tag & (self.size["sets"]-1)
        for block in range(self.size["blocks_per_set"]):
            if self.valid_bits[set, block] == 1 and self.tags[set, block] == tag:
                for word in range(MemorySettings.num_words_per_block):
                    self.contents[set, block, word] = data[word]
                if MemorySettings.cache_is_write_back:
                    self.dirty_bits[set, block] = 1
                self.book_keeping_was_modified = True
                self.book_keeping_modified_set = set
                self.book_keeping_modified_block = block
                self.book_keeping_modified_words.append(word_index)
                return

    def place(self, address, data):
        tag = (address >> int(math.log2(MemorySettings.num_words_per_block)))
        set = tag & (self.size["sets"]-1)
        for block in range(self.size["blocks_per_set"]):
            if self.valid_bits[set][block] == 0:
                for word in range(MemorySettings.num_words_per_block):
                    self.contents[set, block, word] = data[word]
                self.tags[set, block] = tag
                self.valid_bits[set, block] = 1
                self.dirty_bits[set, block] = 0

                self.book_keeping_was_modified = True
                self.book_keeping_modified_set = set
                self.book_keeping_modified_block = block
                for word in range(MemorySettings.num_words_per_block):
                    self.book_keeping_modified_words.append(word)
                break

    def replace(self, address, data):
        tag = (address >> int(math.log2(MemorySettings.num_words_per_block)))
        set = tag & (self.size["sets"]-1)
        if MemorySettings.cache_replacement_policy == "random":
            replaced_block = randrange(self.size["blocks_per_set"])

            OldBlock.was_dirty = self.dirty_bits[set][replaced_block] == 1
            block_data = []
            for word in range(MemorySettings.num_words_per_block):
                block_data.append(int(self.contents[set, replaced_block, word]))
            OldBlock.data = block_data
            OldBlock.address = int(self.tags[set, replaced_block]) << (MemorySettings.num_words_per_block-1)

            for word in range(MemorySettings.num_words_per_block):
                self.contents[set, replaced_block, word] = data[word]
            self.tags[set, replaced_block] = tag
            self.valid_bits[set, replaced_block] = 1
            self.dirty_bits[set, replaced_block] = 0

            self.book_keeping_was_modified = True
            self.book_keeping_modified_set = set
            self.book_keeping_modified_block = replaced_block
            for word in range(MemorySettings.num_words_per_block):
                self.book_keeping_modified_words.append(word)

    def read(self, address):
        tag = (address >> int(math.log2(MemorySettings.num_words_per_block)))
        set = tag & (self.size["sets"]-1)
        for block in range(self.size["blocks_per_set"]):
            if self.tags[set, block] == tag:
                block_data = []
                for word in range(MemorySettings.num_words_per_block):
                    block_data.append(int(self.contents[set, block, word]))
                return block_data

    def set_has_empty_block(self, address):
        has_empty = False
        set = (address >> (MemorySettings.num_words_per_block-1)) & (self.size["sets"]-1)
        for block in range(self.size["blocks_per_set"]):
            if self.valid_bits[set, block] == 0:
                has_empty = True
                break
        return has_empty

    def is_in_cache(self, address):
        available = False
        tag = (address >> int(math.log2(MemorySettings.num_words_per_block)))
        set = tag & (self.size["sets"]-1)
        for block in range(self.size["blocks_per_set"]):
            if self.valid_bits[set, block] == 1 and self.tags[set, block] == tag:
                available = True
                break
        return available


class Memory:
    def __init__(self):
        self.wait_cycles = MemorySettings.memory_wait_cycles
        self.memory = [0] * MEMORY_SIZE
        self.cache = Cache(MemorySettings.num_sets, MemorySettings.num_blocks_per_set, MemorySettings.num_words_per_block)
        self.processing = False
        self.data_ready = True
        self.data_word = 0
        self.word_address = 0
        self.block_address = 0
        self.is_write = False
        self.is_writing_to_mem = False

    def tick(self):
        self.data_ready = False
        self.cache.book_keeping_was_modified = False
        self.cache.book_keeping_modified_words = []
        if self.is_processing():
            if self.is_writing_to_mem:
                self._handle_writing_to_mem()
            elif MemorySettings.cache_active and self.cache.is_in_cache(self.block_address):
                self._handle_read_write_in_cache()
            elif self.wait_cycles == 0:
                self.wait_cycles = MemorySettings.memory_wait_cycles
                self.processing = False
                self.data_ready = True
                if self.is_write:
                    self._handle_write()
                else:
                    self._handle_read()
            else:
                self.wait_cycles = self.wait_cycles - 1

    def _handle_read(self):
        self.data_word = self.memory[self.word_address]
        if MemorySettings.cache_active:
            block_data = []
            for word in range(MemorySettings.num_words_per_block):
                block_data.append(self.memory[self.block_address + word])
            if self.cache.set_has_empty_block(self.block_address):
                self.cache.place(self.block_address, block_data)
            else:
                self.cache.replace(self.block_address, block_data)
                if OldBlock.was_dirty:
                    self.wait_cycles = MemorySettings.memory_wait_cycles
                    self.processing = True
                    self.data_ready = False
                    self.is_writing_to_mem = True
                    OldBlock.was_dirty = False

    def _handle_write(self):
        word_index = self.word_address & (MemorySettings.num_words_per_block - 1)
        block_data = []
        for word in range(MemorySettings.num_words_per_block):
            block_data.append(self.memory[self.block_address + word])
        block_data[word_index] = self.data_word
        if self.cache.set_has_empty_block(self.block_address):
            self.cache.place(self.block_address, block_data)
            self.cache.modify(self.block_address, block_data, word_index)
        else:
            self.cache.replace(self.block_address, block_data)
            self.cache.modify(self.block_address, block_data, word_index)
            if OldBlock.was_dirty:
                self.wait_cycles = MemorySettings.memory_wait_cycles
                self.processing = True
                self.data_ready = False
                self.is_writing_to_mem = True
                OldBlock.was_dirty = False

    def _handle_read_write_in_cache(self):
        self.processing = False
        self.data_ready = True
        block_data = self.cache.read(self.block_address)
        word_index = self.word_address & (MemorySettings.num_words_per_block - 1)
        if self.is_write:
            block_data[word_index] = self.data_word
            self.cache.modify(self.block_address, block_data, word_index)
        else:
            self.data_word = block_data[word_index]

    def _handle_writing_to_mem(self):
        if self.wait_cycles == 0:
            self.wait_cycles = MemorySettings.memory_wait_cycles
            self.processing = False
            self.data_ready = True
            for word in range(MemorySettings.num_words_per_block):
                self.memory[OldBlock.address+word] = OldBlock.data[word]
            self.is_writing_to_mem = False
        else:
            self.wait_cycles = self.wait_cycles - 1

    def read_request(self, address):
        self.is_write = False
        self.processing = True
        self.word_address = address
        self.block_address = self.word_address & 0xffffffff << int(math.log2(MemorySettings.num_words_per_block))

    def write_request(self, address, data):
        self.is_write = True
        self.processing = True
        self.word_address = address
        self.data_word = data
        self.block_address = self.word_address & 0xffffffff << int(math.log2(MemorySettings.num_words_per_block))

    def read_data(self):
        return self.data_word

    def is_processing(self):
        return self.processing

    def is_data_ready(self):
        return self.data_ready
