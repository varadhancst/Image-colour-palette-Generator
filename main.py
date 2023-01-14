import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.image as mpimg
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from PIL import Image
import extcolors
from colormap import rgb2hex
from flask import Flask, render_template, session
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from werkzeug.utils import secure_filename
from flask_bootstrap import Bootstrap
from wtforms import SubmitField
import os
from dotenv import load_dotenv

load_dotenv()


matplotlib.use('agg')

app = Flask(__name__, template_folder='templates', static_folder='static')
Bootstrap(app)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
UPLOAD_FOLDER = os.path.join('static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


class UploadForm(FlaskForm):
    file = FileField(validators=[FileRequired()])
    submit = SubmitField(u'Submit')


def color_to_df(input_image):
    colors_pre_list = str(input_image).replace('([(', '').split(', (')[0:-1]
    df_rgb = [i.split('), ')[0] + ')' for i in colors_pre_list]
    df_percent = [i.split('), ')[1].replace(')', '') for i in colors_pre_list]

    # convert RGB to HEX
    df_color_up = [rgb2hex(int(i.split(", ")[0].replace("(", "")),
                           int(i.split(", ")[1]),
                           int(i.split(", ")[2].replace(")", ""))) for i in df_rgb]

    df = pd.DataFrame(zip(df_color_up, df_percent), columns=["c_code", "occurrence"])
    return df


def exact_color(input_image, resize, tolerance, zoom):
    # background
    bg = 'static/bg.png'
    fig, ax = plt.subplots(figsize=(192, 108), dpi=10)
    fig.set_facecolor('white')
    plt.savefig(bg)
    plt.close(fig)

    # resize
    output_width = resize
    img = Image.open(input_image)
    if img.size[0] >= resize:
        wpercent = (output_width / float(img.size[0]))
        hsize = int((float(img.size[1]) * float(wpercent)))
        img = img.resize((output_width, hsize), Image.Resampling.LANCZOS)
        resize_name = 'resize_' + input_image
        img.save(resize_name)
    else:
        resize_name = input_image

    # crate dataframe
    img_url = resize_name
    colors_x = extcolors.extract_from_path(img_url, tolerance=tolerance, limit=13)
    df_color = color_to_df(colors_x)

    # annotate text
    list_color = list(df_color['c_code'])
    list_precent = [int(i) for i in list(df_color['occurrence'])]
    text_c = [c + ' ' + str(round(p * 100 / sum(list_precent), 1)) + '%' for c, p in zip(list_color, list_precent)]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(160, 120), dpi=10)

    # donut plot
    wedges, text = ax1.pie(list_precent,
                           labels=text_c,
                           labeldistance=1.05,
                           colors=list_color,
                           textprops={'fontsize': 100, 'color': 'black'})
    plt.setp(wedges, width=0.3)

    # add image in the center of donut plot
    img = mpimg.imread(resize_name)
    imagebox = OffsetImage(img, zoom=zoom)
    ab = AnnotationBbox(imagebox, (0, 0))
    ax1.add_artist(ab)

    # color palette
    x_posi, y_posi, y_posi2 = 160, -170, -170
    for c in list_color:
        if list_color.index(c) <= 5:
            y_posi += 180
            rect = patches.Rectangle((x_posi, y_posi), 360, 160, facecolor=c)
            ax2.add_patch(rect)
            ax2.text(x=x_posi + 400, y=y_posi + 100, s=c, fontdict={'fontsize': 120})
        else:
            y_posi2 += 180
            rect = patches.Rectangle((x_posi + 1000, y_posi2), 360, 160, facecolor=c)
            ax2.add_artist(rect)
            ax2.text(x=x_posi + 1400, y=y_posi2 + 100, s=c, fontdict={'fontsize': 120})

    fig.set_facecolor('white')
    ax2.axis('off')
    bg = plt.imread('static/bg.png')
    plt.imshow(bg)
    plt.tight_layout()
    plt.savefig('static/default.jpg')


@app.route('/', methods=['GET', 'POST'])
def home_page(img_path=None):
    form = UploadForm()
    if form.validate_on_submit():
        filename = secure_filename(form.file.data.filename)
        form.file.data.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        # form.file.data.save('uploads/' + filename)
        session['uploaded_img_file_path'] = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        img_file_path = session.get('uploaded_img_file_path', None)
        input_photo = img_file_path
        # input_photo = "static/varadhan.png"
        exact_color(input_photo, 900, 10, 2.5)
        if os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], filename)):
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        img_path = 'static/default.jpg'

    return render_template("index.html", form=form, img=img_path)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
#     app.run(debug=True)
