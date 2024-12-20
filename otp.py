import random
def genotp():
    otp=''
    # cps=[chr(i) for i in range(ord('A'),ord('Z')+1)]
    sma=[chr(i) for i in range(ord('a'),ord('z')+1)]
    # syb=[chr(i) for i in range(ord('#'),ord('@')+1)]
    for i in range(0,3):
        # otp=otp+random.choice(cps)
        otp=otp+random.choice(sma)
        otp=otp+str(random.randint(0,9))
    print(otp)
    return(otp)
print(genotp())