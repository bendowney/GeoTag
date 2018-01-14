import os
from datetime import datetime, timedelta
import json
import numpy as np
import pandas as pd
from PIL import Image
import piexif
from math import floor

def getJpegs(directory):
	jpegs = []
	for filename in os.listdir("./"):
		if filename.upper().endswith(".JPG") or filename.upper().endswith(".JPEG"):
			jpegs.append(filename.upper())
	return jpegs

def readTimelineGPS(filename,start_date,end_date):

	fp = open(filename,'r')

	rawData = json.loads(fp.read())

	fp.close()

	dataFrame = pd.DataFrame(rawData['locations'])

	dataFrame['timestamp'] = pd.to_datetime(dataFrame['timestampMs'], unit='ms')

	dataFrame = dataFrame[ (dataFrame['timestamp'] >= start_date) & (dataFrame['timestamp'] <= end_date) ]

	dataFrame['latitude'] = dataFrame['latitudeE7'] / 10000000
	dataFrame['longitude'] = dataFrame['longitudeE7'] / 10000000

	dataFrame.pop('timestampMs')

	dataFrame.index = dataFrame['timestamp']

	dataFrame = dataFrame[['timestamp', 'latitude', 'longitude', 'altitude', 'heading', 'velocity', 'accuracy', 'verticalAccuracy']]

	return dataFrame

def nearest(items,pivot):
	return min(items, key=lambda x: abs(x - pivot))

def degToDmsRational(degFloat):
  
  minFloat = degFloat % 1 * 60
  secFloat = minFloat % 1 * 60
  deg = floor(degFloat)
  min = floor(minFloat)
  sec = round(secFloat * 100)

  return [(deg, 1), (min, 1), (sec, 100)]

def main():

	timeline_file = "/home/ben/Garage/GeoTag/history.json"

	start_date = datetime.strptime(raw_input("Start date (YYYY-MM-DD): "),"%Y-%m-%d")
	end_date = datetime.strptime(raw_input("End date (YYYY-MM-DD): "),"%Y-%m-%d")

	timeline = readTimelineGPS(timeline_file,start_date,end_date)

	print "Loaded {} timeline records from {} to {}.".format(len(timeline),timeline["timestamp"].values[len(timeline)-1],timeline["timestamp"].values[0])

	files = getJpegs("./")

	offset = input("Enter time offset (in hours):")	

	for file in files:

		print "Reading metadata from image {}".format(file)

		im = Image.open(file)

		exif_dict = piexif.load(im.info["exif"])

		if len(exif_dict["GPS"]) > 0:
			print "Image already contains GPS metadata, skipping"
			print exif_dict["GPS"]
		else:
			print "No GPS metadata found"
			if piexif.ExifIFD.DateTimeOriginal in exif_dict["Exif"]:
				timestamp = datetime.strptime(exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal],'%Y:%m:%d %H:%M:%S')
				print "Searching for a timeline hit around {} with an offset of {} hours".format(timestamp,offset)
				hit = nearest(timeline.index, timestamp + timedelta(hours=offset))
				hit_record = timeline.loc[timeline['timestamp'] == hit]
				print "Closest timeline hit is {}, {} difference".format(hit,timestamp-hit)
				print "Location: {}, {}".format(hit_record["latitude"].values[0], hit_record["longitude"].values[0])


				lat = hit_record["latitude"].values[0]
				if lat < 0:
					lat_ref = 'S' 
					lat = lat * -1
				else:
					lat_ref = 'N' 

				lat_rational = degToDmsRational(lat)


				lng = hit_record["longitude"].values[0]
				if lng < 0:
					lng_ref = 'W'
					lng = lng * -1
				else:
					lng_ref = 'E'	
				lng_rational = degToDmsRational(lng)

				exif_dict["GPS"] = {
				piexif.GPSIFD.GPSLatitudeRef: lat_ref,
				piexif.GPSIFD.GPSLatitude:  lat_rational ,
				piexif.GPSIFD.GPSLongitudeRef: lng_ref,
				piexif.GPSIFD.GPSLongitude:  lng_rational 
				}

				print exif_dict["GPS"]

				exif_bytes = piexif.dump(exif_dict)

				im.save(file, "jpeg", exif=exif_bytes)

			else:
				print "Cannot identify original photo timestamp, skipping"

		im.close()

		print ""

if __name__ == "__main__":
	main()


