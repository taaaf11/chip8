import pygame

pygame.init()

# screen = pygame.display.set_mode((1280,720))
# screen = pygame.display.set_mode((64 * 8, 32 * 8))
screen = pygame.display.set_mode((64, 32))

clock = pygame.time.Clock()

instructions = 0x1011


def predef_list(size):
    return [0 for _ in range(size)]


class Chip8:
    def __init__(self):
        self.memory = [0 for _ in range(4096)]
        self.registers = [0 for _ in range(16)]
        self.program_counter = 0x200
        self.index_register = 0x0
        self.delay_timer = 0xFF
        self.sound_timer = 0xFF
        self.stack = []
        self.display_array = [
            [0 for _ in range(64)]
            
            for __ in range(32)
        ]
        
    def load_program(self, file_path):
        i = 0x200
        with open(file_path, "rb") as f:
            while value := f.read(1):
                self.memory[i] = int(value[0])
                i+=1
        
    def black_the_screen(self):
        # just create a new array and slap it into the variable
        # instead of changing each index
        self.display_array = [
            [0 for _ in range(64)]
            
            for __ in range(32)
        ]
        
    def do_the_main_loop(self):
        while True:
            # Process player inputs.
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    raise SystemExit

            # Do logical updates here.
            # ...

            self.exec_next_instruction()
            
            for y in range(len(self.display_array)):
                for x in range(len(self.display_array[0])):
                    if self.display_array[y][x] == 1:
                        screen.set_at((x, y), (255, 255, 255))
                    else:
                        screen.set_at((x, y), (0,0,0))
        
            # Render the graphics here.
            # ...

            pygame.display.flip()  # Refresh on-screen display
            clock.tick(60)         # wait until next frame (at 60 FPS)
            
    def load_font_file(self):
        a = [0xF0, 0x90, 0x90, 0x90, 0xF0, # 0
            0x20, 0x60, 0x20, 0x20, 0x70, # 1
            0xF0, 0x10, 0xF0, 0x80, 0xF0, # 2
            0xF0, 0x10, 0xF0, 0x10, 0xF0, # 3
            0x90, 0x90, 0xF0, 0x10, 0x10, # 4
            0xF0, 0x80, 0xF0, 0x10, 0xF0, # 5
            0xF0, 0x80, 0xF0, 0x90, 0xF0, # 6
            0xF0, 0x10, 0x20, 0x40, 0x40, # 7
            0xF0, 0x90, 0xF0, 0x90, 0xF0, # 8
            0xF0, 0x90, 0xF0, 0x10, 0xF0, # 9
            0xF0, 0x90, 0xF0, 0x90, 0x90, # A
            0xE0, 0x90, 0xE0, 0x90, 0xE0, # B
            0xF0, 0x80, 0x80, 0x80, 0xF0, # C
            0xE0, 0x90, 0x90, 0x90, 0xE0, # D
            0xF0, 0x80, 0xF0, 0x80, 0xF0, # E
            0xF0, 0x80, 0xF0, 0x80, 0x80]  # F
        
        
        for i, value in enumerate(a):
            self.memory[0x300 + i] = value
    
    def exec_next_instruction(self):
        # mine:
        # instruction = self.memory[self.program_counter]
        
        # chatgpt
        high = self.memory[self.program_counter]
        low  = self.memory[self.program_counter + 1]
        instruction = (high << 8) | low
        
        match instruction & 0xF000:
            # in this case, there can only be two instructions
            # 00E0 : for clear screen
            # 00EE : for returning the current function
            # so we just need to fetch second byte
            case 0x0000:
                second_byte = instruction & 0x00FF
                match second_byte:
                    case 0xE0:
                        self.black_the_screen()
                        self.program_counter += 2
                    case 0xEE:
                        self.program_counter = self.stack.pop()
                        
            
            # jump :'(
            case 0x1000:
                address = instruction & 0x0FFF
                self.program_counter = address
                print(f"Executing jump to: {address}")
            
            # set register to value            
            case 0x6000:
                # logic:
                # we only want the second nibble
                # (bits in the second hex digit), so we mask 
                # with other nibbles set to 0.
                # after this, we need to shift right by 8 bits
                # because, we want the nibble at the second position,
                # but currently the result also contains
                # 8 rightmost 0 bits from bitwise AND
                
                # example:
                # let's say original instruction was
                # 0x6233
                
                # we masked the original to check if it falls
                # under 0x6000, which it did that's why
                # we are in this block.
                
                # now we want the register whose value we
                # want to set to 33 (in hex). it is 2,
                # the second hexadecimal digit in the instruction
                
                # now, just only masking will not help.
                
                # to get the second digit, we mask with 0x0F00
                # this will remove the first and the last two 
                # hexa digits,
                # leaving with 0x0200,
                
                # but we really wanted 2, not 0x200.
                # to remove these last two zeroes, we rightshift
                # by 8 bits.
                
                register = (instruction & 0x0F00) >> 8
                
                value = instruction & 0x00FF
                self.registers[register] = value
                
                self.program_counter += 2
            
            # add value to register
            case 0x7000:
                register = (instruction & 0x0F00) >> 8
                value = instruction & 0x00FF
                self.registers[register] += value
                
                self.program_counter += 2
                
            case 0xA000:
                value = instruction & 0x0FFF
                self.index_register = value
                self.program_counter += 2
            
            # 0x DXYN                
            case 0xD000:
                vX = (instruction & 0x0F00) >> 8
                vY = (instruction & 0x00F0) >> 4
                N  = instruction & 0x000F
                
                startX = self.registers[vX] & 63
                startY = self.registers[vY] & 31
                X = startX
                Y = startY
                
                self.program_counter += 2
                
                self.registers[-1] = 0
                
                for row in range(N):
                    
                    if Y >= 32:
                        break
                    sprite_data = self.memory[self.index_register + row]
                    bits = str(bin(sprite_data))[2:]
                    # if the bits are less than 8, we fill
                    # the leftmost bits with zeros
                    bits = bits.rjust(8, '0')
                    
                    X = startX
                    
                    for bit in bits:
                        if X >= 64:
                            break
                        if bit == '1':
                            if self.display_array[Y][X] == 1:
                                self.display_array[Y][X] = 0
                                self.registers[-1] = 1
                            else:
                                self.display_array[Y][X] = 1
                        X+=1
                        
                    Y += 1
                    
            case 0x8000:
                vX = (instruction & 0x0F00) >> 8
                vY = (instruction & 0x00F0) >> 4
                last_nip = instruction & 0x000F
                X = self.registers[vX]
                Y = self.registers[vY]
                self.program_counter += 2
                # this instruction class contains arithmetic and
                # logiical instructions:
                
                # 8XY1: Binary OR
                # 8XY2: Binary AND
                # 8XY3: Logical XOR
                # 8XY4: Add etc.
                
                match last_nip:
                    # set
                    case 0x0:
                        self.registers[vX] = self.registers[vY]
                    
                    # binary or
                    case 0x1:
                        self.registers[vX] |= self.registers[vY]
                        
                    # binary and
                    case 0x2:
                        self.registers[vX] &= self.registers[vY]
                    
                    # logical xor           
                    case 0x3:
                        self.registers[vX] ^= self.registers[vY]
                        
                    # add
                    case 0x4:
                        result = self.registers[vX] + self.registers[vY]
                        result_bits = str(bin(result))[2:]
                        # if overflow
                        if len(result_bits) > 8:
                            result_bits = result_bits[len(result_bits) - 8:]
                            self.registers[-1] = 1
                        result = int(result_bits)
                        self.registers[vX] = result
                    
                    # vx = vx - vy
                    case 0x5:
                        result = self.registers[vX] - self.registers[vY]
                        
                        if self.registers[vX] > self.registers[vY]:
                            self.registers[-1] = 1
                        self.registers[vX] = result
                        
                    # vx = vy - vx
                    case 0x7:
                        result = self.registers[vY] - self.registers[vX]
                        
                        if self.registers[vY] > self.registers[vX]:
                            self.registers[-1] = 1
                        self.registers[vX] = result
                        
            case 0x8000:
                vX = (instruction & 0x0F00) >> 8
                vY = (instruction & 0x00F0) >> 4
                last_nibble = (instruction & 0x000F)
                self.program_counter += 2
                
                match last_nibble:
                    case 0x6:
                        bit_to_remove = self.registers[vX] & 0x01
                        self.registers[vX] >>= 1
                        self.registers[-1] = bit_to_remove
                    case 0xE:
                        bit_to_remove = self.registers[vX] & 0x80
                        self.registers[vX] <<= 1
                        self.registers[-1] = bit_to_remove
            
            case 0xA000:
                value = instruction & 0x0FFF
                self.index_register = value
                self.program_counter += 2
                
                    
    
        
screen.fill("black")  # Fill the display with a solid color


chip8 = Chip8()
# chip8.load_program("binfile.dat")
# chip8.load_program("forever.dat")
# chip8.load_program("second")

# chip8.load_program("thired")
# chip8.memory[0x300] = 0xF0
chip8.load_font_file()
# chip8.load_program("fourd")
chip8.load_program("ibmlogo.ch8")
chip8.do_the_main_loop()
