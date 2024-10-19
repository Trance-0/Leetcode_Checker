""" Random key generator

"""
import random

def generate_random_string(length:int = 10)-> str:
    """ Generate random key with length

    Attribute:
        characters: the character set of 
    
    Args:
        length: default generate code with length 10

    Returns:
        random string with give size
    
    """
    characters = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ@#$%^!&-+=()'
    n=len(characters)
    res=''
    for _ in range(length):
        res+=characters[random.randint(0,n-1)]
    return res

print(generate_random_string(64))