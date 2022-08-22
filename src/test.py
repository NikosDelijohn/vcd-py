import multiprocessing as mp
import time 

def func(val):
    print(f"f {val}")
    time.sleep(0.5)
    return val

def main():

    with mp.Pool(processes=4) as pool: 

        for el in pool.imap(func, range(0,1000),chunksize=10): 
            print("l ",el)


if __name__ == "__main__":
    main()