# Localize
import locale
locale.setlocale(locale.LC_TIME, "id_ID") # Indonesia
import datetime


from flask import Flask
from flask_sqlalchemy import SQLAlchemy

apl = Flask(__name__, template_folder='../', static_folder='../assets/')
apl.config['SECRET_KEY'] = 'R4H4514_B4N633DD!@#$'
apl.config['CSRF_ENABLED'] = True
apl.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@127.0.0.1:3306/flasks?charset=utf8mb4'
apl.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

#### Constanta ####

db = SQLAlchemy(apl)


### Consruct ###

def min_diff(start, end):
    """Cek selisih waktu dalam menit. Jika menerapakan pada struktur
    aplikasi 'factory', masukkan ke dalam file Models."""

    diff = (end - start).total_seconds() / 60
    return diff


def time_crash(x_start, x_end, y_start, y_end):
    """Memeriksa jenis-jenis bentrok waktu. Jika menerapakan pada struktur
    aplikasi 'factory', masukkan ke dalam file Models."""

    if ( (x_start > y_start) and (x_start < y_end) and (min_diff(x_start, y_end) >= 0) ) :
        return True
    elif ( (x_end > y_start) and (x_end < y_end) and (min_diff(y_start, x_end) >= 0) ) :
        return True
    elif ( (x_start >= y_start) and (x_start < y_end) and (x_end > y_start) and (x_end <= y_end) ) :
        return True
    elif ( (x_start <= y_start) and (x_start < y_end) and (x_end > y_start) and (x_end >= y_end) ) :
        return True
    else :
        return False


#### Models ####

class DateTimeRange(db.Model):
    __tablename__ = 'datetime_range'

    id = db.Column('id', db.Integer(), primary_key=True)
    description = db.Column('description', db.String(191), index=True)
    location = db.Column('location', db.String(191), index=True)
    crash = db.Column('crash', db.Boolean(), default=False)
    start = db.Column('start', db.DateTime())
    end = db.Column('end', db.DateTime())

    def __repr__(self):
        return "(Kegiatan :{}({}), Lokasi:{}, Mulai:{}, Selesai:{})".format(
            self.description, self.id, self.location, self.start, self.end
        )

    def start_end_day(self, back=0, forward=0):
        """Menentukan jam awal dan jam akhir dari hari.
        Efisiensi penyaringan kueri."""

        start = self.start.replace(hour=0,minute=0,second=0) - datetime.timedelta(days=back)
        end = self.start.replace(hour=23,minute=59,second=59) + datetime.timedelta(days=forward)
        return start, end

    def crash_with(self, start=0, end=0):
        """Mengecek semua kegiatan berpotensi bentrok di hari yang sama"""

        query = DateTimeRange.query.filter( (DateTimeRange.location == self.location) \
            & (DateTimeRange.start > self.start_end_day(start,end)[0]) & \
            (DateTimeRange.end < self.start_end_day(start,end)[1]) ).order_by( DateTimeRange.start.asc() ).all()
        """Eliminasi obyek diri sendiri"""
        cleaning = []
        for i in query:
            if ( self.id != i.id ):
                cleaning.append(i)

        crash_item = []
        for j in cleaning:
            if ( time_crash(self.start, self.end, j.start, j.end) == True ):
                crash_item.append(j)

        return crash_item

    def has_crash(self, start=0, end=0):
        """Memeriksa kegiatan dari terjadinya bentrok. Memberikan status
        bentrok menjadi True """

        if len(self.crash_with(start, end)) > 0:
            self.crash = True
            db.session.commit()
            return True
        else :
            self.crash = False
            db.session.commit()
            return False


#### Forms ####

from flask_wtf import Form as Formulir
from wtforms import ( 
    StringField, SubmitField, DateTimeField, HiddenField,
    SelectField, BooleanField,
)
from wtforms.validators import (
    Optional, DataRequired,
)

class DateRangeFormulir(Formulir):
    description = StringField('Deskripsi', validators=[DataRequired(message='Harap diisi')])
    location = SelectField(
        'Lokasi', coerce=int, choices=[],
        validators=[DataRequired(message='Harap diisi')]
    )
    start = HiddenField('Mulai')
    end = HiddenField('Selesai')
    simpan = SubmitField('Simpan')


#### Controllers ####

from flask import (
    request, render_template, flash, redirect, url_for, jsonify,
)

@apl.route('/', defaults={'start':365, 'end':365})
def index(start,end):
    data = DateTimeRange.query.order_by(DateTimeRange.start.asc()).all()

    # memaksa update status bentrok setiap mengakses daftar data
    # hal ini mengakibatkan proses pemuatan data yang lama
    # untuk efisiensi bisa dikembangkan dengan penyaringan kueri
    # dengan rentang waktu tertentu
    for i in data:
        i.has_crash(start,end)

    formulir = DateRangeFormulir()
    return render_template(
        'datetime-range/index.html',
        data=data,
        start=start,
        end=end,
        formulir=formulir
    )

@apl.route('/edit/data/', defaults={'mode': 0, 'id': 0}, methods=['GET', 'POST'])
@apl.route('/edit/<int:mode>/data/<int:id>/', methods=['GET', 'POST'])
def edit(mode, id):
    formulir = DateRangeFormulir()
    data = DateTimeRange()

    # mengambil form select
    location_choice = [
        ('1', 'Ruang Sahardjo'),
        ('2', 'Ruang Soepomo'),
        ('3', 'Ruang Ismail Saleh')
    ]
    formulir.location.choices = location_choice

    def custom_form_validation():
        """karena bootstrap daterangepicker tidak dapat divalidasi
        dari backend maka harus mengalah dengan memvalidasi satu persatu
        form-form selain daterangepicker. So sick :'( """

        formulir.description.validate(formulir.description)
        formulir.location.validate(formulir.location)


    if mode == 0 : # mode create
        if formulir.is_submitted():
            custom_form_validation()

            # insert database
            data = DateTimeRange(description=formulir.description.data)
            data.location = formulir.location.data
            data.start = datetime.datetime.strptime(formulir.start.data, '%Y-%m-%d %H:%M')
            data.end = datetime.datetime.strptime(formulir.end.data, '%Y-%m-%d %H:%M')
            db.session.add(data)
            db.session.commit()

            # UX info
            if data.has_crash() == True :
                for i in data.crash_with():
                    flash('Jadwal kegiatan berpotensi bentrok dengan \
                        <a class="badge badge-danger" href="'+ url_for('edit', mode=1, id=i.id) +\
                        '">' + i.description + '</a><br/> Jika ingin memperbaiki jadwal, \
                        klik <a class="badge badge-primary" href="'+ url_for('edit', mode=1, id=data.id) + \
                        '">di sini</a>', category='warning')
            flash('Jadwal kegiatan berhasil ditambahkan.', category='sukses')
            return redirect( url_for('index') )


    elif mode == 1 : # mode edit
        data = DateTimeRange.query.get_or_404(id)

        # mengambil data, inisialisasi ke dalam form
        formulir.description.default = data.description
        formulir.location.default = data.location
        formulir.start.default = data.start.strftime('%A, %d/%B/%y %H:%M')
        formulir.end.default = data.end.strftime('%A, %d/%B/%y %H:%M')

        if formulir.is_submitted():
            custom_form_validation()

            # antisipasi bug daterangepicker ketika tidak terjadi perubahan
            if ( formulir.start.data == data.start.strftime('%A, %d/%B/%y %H:%M') ):
                formulir.start.data = datetime.datetime.strftime(data.start, '%Y-%m-%d %H:%M')
            if ( formulir.end.data == data.end.strftime('%A, %d/%B/%y %H:%M') ):
                formulir.end.data = datetime.datetime.strftime(data.end, '%Y-%m-%d %H:%M')

            # updating database
            data.description = formulir.description.data
            data.location = formulir.location.data
            data.start = datetime.datetime.strptime(formulir.start.data, '%Y-%m-%d %H:%M')
            data.end = datetime.datetime.strptime(formulir.end.data, '%Y-%m-%d %H:%M')
            db.session.commit()

            # UX info
            if data.has_crash() == True :
                for i in data.crash_with():
                    flash('Jadwal kegiatan berpotensi bentrok dengan \
                        <a class="badge badge-danger" href="'+ url_for('edit', mode=1, id=i.id) +\
                        '">' + i.description + '</a><br/> Jika ingin memperbaiki jadwal, \
                        klik <a class="badge badge-primary" href="'+ url_for('edit', mode=1, id=data.id) + \
                        '">di sini</a>', category='warning')
            flash('Jadwal kegiatan berhasil diubah.', category='sukses')

            return redirect( url_for('index') )

    elif mode == 2: # mode delete
        if formulir.is_submitted():
            data = DateTimeRange.query.get_or_404(id)
            db.session.delete(data)
            db.session.commit()

            # UX info
            flash('Jadwal berhasil dihapus.', category='sukses')

            return redirect( url_for('index') )

    # render form
    formulir.process()

    return render_template('datetime-range/edit.html', formulir=formulir, mode=mode, data=data)


#### Customizing ####

@apl.after_request
def add_header(r):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'
    return r

#### Execute App ####

if __name__ == '__main__':
    apl.run(debug=True)
