# Localize
import locale
locale.setlocale(locale.LC_TIME, "id_ID") # Indonesia
import datetime


from flask import Flask
from flask_sqlalchemy import SQLAlchemy

apl = Flask(__name__, template_folder='../', static_folder='../assets/')
apl.config['SECRET_KEY'] = 'R4H4514_B4N633DD!@#$'
apl.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@127.0.0.1:3306/flasks?charset=utf8mb4'
apl.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

#### Constanta ####

db = SQLAlchemy(apl)


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
        return "Kegiatan :{}, Lokasi:{}, Mulai:{}, Selesai:{}".format(
            self.description,self.location, self.start, self.end
        )


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

@apl.route('/')
def index():
    data = DateTimeRange.query.order_by(DateTimeRange.start.asc()).all()
    formulir = DateRangeFormulir()
    return render_template('datetime-range/index.html', data=data, formulir=formulir)

@apl.route('/edit/data/', defaults={'mode': 0, 'id': 0}, methods=['GET', 'POST'])
@apl.route('/edit/<int:mode>/data/<int:id>/', methods=['GET', 'POST'])
def edit(mode, id):
    formulir = DateRangeFormulir()

    # mengambil form select
    location_choice = [
        ('1', 'Ruang Sahardjo'),
        ('2', 'Ruang Soepomo'),
        ('3', 'Ruang Ismail Saleh')
    ]
    formulir.location.choices = location_choice

    def custom_form_validation():
        # karena bootstrap daterangepicker tidak dapat divalidasi dari backend
        # maka harus mengalah memvalidasi satu persatu form2 selain daterangepicker
        # so sick :'(
        formulir.description.validate(formulir.description)
        formulir.location.validate(formulir.location)

    def check_crash(obyek):
        for i in DateTimeRange.query.filter( (DateTimeRange.location==obyek.location) & \
            (DateTimeRange.start > datetime.date.today()) ).order_by(DateTimeRange.start.asc()).all():
            if (obyek.start.day == i.start.day and obyek.start.year == i.start.year):
                if ( obyek.id != i.id ):
                    if (obyek.start.hour >= i.start.hour and obyek.start.hour <= i.end.hour ) or \
                        (obyek.end.hour >= i.start.hour and obyek.end.hour <= i.end.hour):
                        flash('Jadwal kegiatan berpotensi tabrakan dengan \
                            <a class="badge badge-danger" href="'+ url_for('edit', mode=1, id=i.id) +\
                            '">' + i.description + '</a><br/> Jika ingin memperbaiki jadwal, \
                            klik <a class="badge badge-primary" href="'+ url_for('edit', mode=1, id=obyek.id) + \
                            '">di sini</a>', category='warning')
                        return True
                        break
                    else:
                        return False
                else:
                    pass


    if mode == 0 : # mode create
        if formulir.is_submitted():
            custom_form_validation()

            # insert database
            data = DateTimeRange(description=formulir.description.data)
            data.location = formulir.location.data
            data.start = datetime.datetime.strptime(formulir.start.data, '%Y-%m-%d %H:%M')
            data.end = datetime.datetime.strptime(formulir.end.data, '%Y-%m-%d %H:%M')
            data.crash = check_crash(data)
            db.session.add(data)
            db.session.commit()

            # UX info
            flash('Jadwal kegiatan berhasil ditambahkan.', category='sukses')
            return redirect( url_for('index') )
            # return str(check_crash(data))

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
                # formulir.start.data = data.start
                formulir.start.data = datetime.datetime.strftime(data.start, '%Y-%m-%d %H:%M')
            if ( formulir.end.data == data.end.strftime('%A, %d/%B/%y %H:%M') ):
                # formulir.end.data = data.end
                formulir.end.data = datetime.datetime.strftime(data.end, '%Y-%m-%d %H:%M')

            # updating database
            data.description = formulir.description.data
            data.location = formulir.location.data
            data.start = datetime.datetime.strptime(formulir.start.data, '%Y-%m-%d %H:%M')
            data.end = datetime.datetime.strptime(formulir.end.data, '%Y-%m-%d %H:%M')
            data.crash = check_crash(data)
            db.session.commit()

            # UX info
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

    return render_template('datetime-range/edit.html', formulir=formulir)


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
