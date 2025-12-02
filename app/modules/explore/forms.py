from flask_wtf import FlaskForm
from wtforms import DateField, SelectField, SelectMultipleField, StringField, SubmitField
from wtforms.validators import Optional
from wtforms.widgets import CheckboxInput, ListWidget

from app.modules.dataset.models import PublicationType

class ExploreForm(FlaskForm):
    submit = SubmitField("Submit")

class MultiCheckboxField(SelectMultipleField):
    widget = ListWidget(prefix_label=False)
    option_widget = CheckboxInput()

class DatasetAdvancedSearchForm(FlaskForm):
    # Búsqueda por texto general
    query = StringField("Search", validators=[Optional()])

    # Filtros por autores
    authors = StringField(
        "Author(s)", validators=[Optional()], render_kw={"placeholder": "Search by author name or ORCIDs"}
    )

    # Filtros por tags
    tags = StringField("Tags", validators=[Optional()], render_kw={"placeholder": "Enter tags separated by commas"})

    # Filtros por tipo de publicación
    publication_types = MultiCheckboxField("Publication Types", coerce=str, validators=[Optional()])

    # Filtros por fecha
    date_from = DateField("From", validators=[Optional()])
    date_to = DateField("To", validators=[Optional()])

    # Ordenamiento
    sort_by = SelectField(
        "Sort by",
        choices=[
            ("created_at_desc", "Newest first"),
            ("created_at_asc", "Oldest first"),
            ("download_count_desc", "Most downloaded"),
            ("title_asc", "Title A-Z"),
            ("title_desc", "Title Z-A"),
        ],
        default="created_at_desc",
    )

    submit = SubmitField("Search")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Poblar las opciones de tipos de publicación
        self.publication_types.choices = [
            (pub_type.value, pub_type.name.replace("_", " ").title())
            for pub_type in PublicationType
            if pub_type != PublicationType.NONE
        ]
