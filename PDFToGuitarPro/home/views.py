from django.shortcuts import render
from django.http import HttpResponse
import cv2
import music21
import guitarpro as gp
from pdf2image import convert_from_path
from django.core.files.storage import FileSystemStorage
import numpy as np
import os
import tempfile
import subprocess

def process_image(image):
    # Convert the image to grayscale
    gray_image = cv2.cvtColor(np.array(image), cv2.COLOR_BGR2GRAY)

    # Apply adaptive thresholding
    thresholded_image = cv2.adaptiveThreshold(gray_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)

    return thresholded_image


def image_to_musicxml(image):
    # Save the processed image to a temporary file
    temp_image_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    cv2.imwrite(temp_image_file.name, image)

    # Create a temporary MusicXML output file
    temp_musicxml_file = tempfile.NamedTemporaryFile(delete=False, suffix=".xml")

    # Call Audiveris command-line interface to process the image and generate a MusicXML file
    audiveris_path = "path/to/audiveris"  # Update this path to your Audiveris installation
    subprocess.run([audiveris_path, "-input", temp_image_file.name, "-output", temp_musicxml_file.name])

    # Close and delete the temporary image file
    temp_image_file.close()
    os.unlink(temp_image_file.name)

    return temp_musicxml_file.name


def convert_score_to_guitar_pro(score):
    # Create a new Guitar Pro file
    gp_file = gp.GuitarProFile()

    # Create a new track
    track = gp.Track(gp_file)
    gp_file.tracks.append(track)

    # Create a new measure and add it to the track
    measure = gp.Measure(track)
    track.measures.append(measure)

    # Create a new voice and add it to the measure
    voice = gp.Voice(measure)
    measure.voices.append(voice)

    # Iterate through the notes in the music21 score and add them to the Guitar Pro file
    for note in score.flat.notes:
        if isinstance(note, music21.note.Note):
            # Convert the music21 note to a Guitar Pro note
            gp_note = gp.Note(gp.Beat(voice), value=int(note.pitch.ps), velocity=95)

            # Create a new beat and add the note to it
            beat = gp.Beat(voice)
            beat.notes.append(gp_note)
            beat.duration = gp.Duration(value=note.duration.quarterLength)
            beat.status = gp.BeatStatus.normal
            beat.effect = gp.BeatEffect(beat)

            # Add the beat to the voice
            voice.beats.append(beat)

    return gp_file

def pdf_to_images(pdf_path):
    # Convert PDF to a list of images
    return convert_from_path(pdf_path)

def read_musicxml_file(file_path):
    # Read MusicXML file using music21
    return music21.converter.parse(file_path)

def write_guitar_pro_file(gp_file, output_file_path):
    # Write the Guitar Pro file to disk
    gp.write(gp_file, output_file_path)


def home(request):
    return render(request, 'index.html')

def upload_pdf(request):
    if request.method == 'POST':
        pdf_file = request.FILES['pdf']
        fs = FileSystemStorage()
        input_pdf_path = fs.save(pdf_file.name, pdf_file)
        output_gp_path = "output.gp5"  # Path to the output Guitar Pro file

        # Convert PDF to images
        images = pdf_to_images(input_pdf_path)

        # Process and recognize music in the images
        musicxml_files = []
        for image in images:
            processed_image = process_image(image)
            musicxml_file = image_to_musicxml(processed_image)
            musicxml_files.append(musicxml_file)

        # Combine the recognized music into a single music21 score
        combined_score = music21.stream.Score()
        for musicxml_file in musicxml_files:
            score = read_musicxml_file(musicxml_file)
            combined_score.insert(0, score)

        # Convert the combined score to a Guitar Pro file
        gp_file = convert_score_to_guitar_pro(combined_score)

        # Write the Guitar Pro file to disk
        write_guitar_pro_file(gp_file, output_gp_path)

        # Remove the uploaded PDF file after processing
        fs.delete(input_pdf_path)

        return HttpResponse('PDF upload and processing was successful.')
    else:
        return render(request, 'upload.html')
