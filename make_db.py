import model
import argparse

def argparser():
    parser = argparse.ArgumentParser()
    parser.add_argument("INPUT", help="XML or XML.GZ file to parse as input")
    parser.add_argument("DATABASE", help="path to create database")
    args = parser.parse_args()
    return(args.INPUT, args.DATABASE)

def main(datapath, dbpath):
    model.create_db(datapath, dbpath)

if __name__ == "__main__":
    main(*argparser())
