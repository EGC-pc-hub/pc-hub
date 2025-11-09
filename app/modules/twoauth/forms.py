from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length, Regexp


class TwoAuthVerifyForm(FlaskForm):
    code = StringField(
        "Código de verificación",
        validators=[DataRequired(), Length(min=6, max=6), Regexp(r"^\d{6}$", message="Introduce 6 dígitos")],
    )
    submit = SubmitField("Verificar")
