from Parse import parse_level
from multiprocessing import Pool
import argparse

if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("filename", type=str, help="Site file name")
  parser.add_argument('cores', nargs='?', default=2, type=int, help="No. cores")

  args = parser.parse_args()

  filename = args.filename
  cores = args.cores
  site_file = open(filename, 'r')
  urls = [x.strip() for x in site_file.readlines()]

  pool = Pool(processes=cores)
  result = pool.map(parse_level, urls)
