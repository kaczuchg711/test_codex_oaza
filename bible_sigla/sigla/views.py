from __future__ import annotations

from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import FormView

from .forms import ImageUploadForm
from .utils import SiglaExtractionError, extract_text, find_references, resolve_references


class UploadView(FormView):
    template_name = "sigla/upload.html"
    form_class = ImageUploadForm
    success_url = reverse_lazy("sigla:upload")

    def form_valid(self, form: ImageUploadForm):
        image_file = form.cleaned_data["image"]

        try:
            text = extract_text(image_file)
        except SiglaExtractionError as error:
            messages.error(self.request, str(error))
            return self.form_invalid(form)

        references = find_references(text)
        results = resolve_references(references)

        if not results:
            messages.warning(
                self.request,
                "Nie udało się znaleźć sigli w przesłanym materiale.",
            )

        context = self.get_context_data(
            form=form,
            results=results,
            extracted_text=text,
            references=references,
        )
        return self.render_to_response(context)

    def form_invalid(self, form):  # type: ignore[override]
        messages.error(self.request, "Popraw proszę błędy w formularzu.")
        return super().form_invalid(form)
