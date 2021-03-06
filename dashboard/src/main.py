"""
putting all things together
"""
import datetime
import os
from pprint import pprint
from google.cloud import storage


# RUn Directly
# from nlp_analytics import NLPAnalytics
# from video_intellegence import ParseVideo
# from video_search import VideoSearch
# from video_to_text import VideoToText
# from vision_analytics import VisionAnalytics
# from config import video_name, local_video_folder, video_frames_folder, local_tmp_folder, clean_folders


from .nlp_analytics import NLPAnalytics
from .video_intellegence import ParseVideo
from .video_search import VideoSearch
from .video_to_text import VideoToText
from .vision_analytics import VisionAnalytics
from .config import local_video_folder, video_frames_folder, local_tmp_folder, clean_folders,gcs_bucket


class VideoIntelligenceRunner(object):
    def __init__(self):
        self.data = {}

    def main(self, query='',video_name='Here_how_Trump_North_Korea_summit_failed.mp4',video_button='english'):
        # return fixture_data

        #clean_folders()


        ## checking for pre processed files and returning
        client = storage.Client()
        bucket = client.get_bucket(gcs_bucket)
        archived_processed_data = video_name + '.txt'
        # archived_processed_data = "Here_how_Trump_North_Korea_summit_failed.mp4" + '.txt'
        blob = bucket.blob('processed_data/' + archived_processed_data)

        if blob.exists():
            print("Processed data exists and returning from cache")
            blob.download_to_filename('data.txt')
            with open('data.txt') as json_file:
                import json
                read_data = json.load(json_file)
            self.data = read_data
            print("Return from cache for video " + video_name)
            return self.data

        ## no processed fiels exists

        print("Starting Video Processing for video",video_name, datetime.datetime.now())
        video_parse = ParseVideo(video_name)
        process_video_data = video_parse.run()
        print("Finished Video Processing", datetime.datetime.now())

        self.data['video_analytics'] = process_video_data
        print(self.data)
        self.data['vision_analytics'] = {}

        for image in process_video_data['frame_images']:
            image_path = os.path.join(local_tmp_folder,video_frames_folder, image)
            vanalytics = VisionAnalytics(image_path)
            vision_data = vanalytics.run()
            print("Statring vision analytics on ")
            self.data['vision_analytics'][image]= vision_data;

        if(video_button=='english'):
            video_encoding ="en-US"
        else:
            video_encoding="hi-IN"

        print("Starting Speech Analytics")
        video_abs_path = video_name
        vtext = VideoToText(video_abs_path,video_encoding)
        vspeechdata = vtext.run()
        self.data['speech_analytics'] = vspeechdata
        print(self.data)
        print("Finished Speech Analytics")

        if(video_encoding == "en-US"):
            print("Starting NLP analytics")
            nlp_ana = NLPAnalytics()
            nlp_data = nlp_ana.entities_text(vspeechdata['transcript'])
            self.data['nlp_analytics'] = nlp_data
            print(self.data['nlp_analytics'])
            print("Finished NLP Analytics")


        words = self.data['speech_analytics']['words']

        self.search(video_abs_path, words,query)
        # self.search(video_abs_path, words, "trump")

        self.data = dict(self.data)
        pprint(self.data)

        import json
        with open('data.txt', 'w') as outfile:
            json.dump(self.data, outfile)

        print("uploading processed data to storage")
        archived_processed_data = video_name + '.txt'
        blob = bucket.blob('processed_data/' + archived_processed_data)
        blob.upload_from_filename('data.txt')

        return self.data

    def search(self, video_abs_path, words, query):
        if query:
            print("Starting search analytics ")
            vsearch = VideoSearch(video_abs_path, query)
            vsearch_data = vsearch.search(words)
            self.data['search_data'] = vsearch_data
            print(self.data)
            print("Finished Search Analytics")
        else:
            self.data['search_data'] = "Pass query to search"
        return {'search_data': self.data['search_data']}


if __name__ == '__main__':
    vrunner = VideoIntelligenceRunner()
    vrunner.main(query='kim')


