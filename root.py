from Parse import parse_root_threaded
import argparse

if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("filename", type=str, help="Site file name")
  args = parser.parse_args()

  filename = args.filename
  site_file = open(filename, 'r')
  urls = [x.strip() for x in site_file.readlines()]
  parse_root_threaded(urls)
