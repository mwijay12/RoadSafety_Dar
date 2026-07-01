from django.db import migrations


def backfill_junction_slugs(apps, schema_editor):
    from django.utils.text import slugify
    Junction = apps.get_model("accidents", "Junction")
    for j in Junction.objects.iterator():
        if j.slug:
            continue
        base = slugify(j.name)[:100]
        slug = base
        counter = 1
        while Junction.objects.filter(slug=slug).exclude(pk=j.pk).exists():
            counter += 1
            slug = f"{base}-{counter}"
        j.slug = slug
        j.save(update_fields=["slug"])


def backfill_h3_cells(apps, schema_editor):
    Accident = apps.get_model("accidents", "Accident")
    try:
        import h3
    except ImportError:
        return
    for a in Accident.objects.iterator():
        if a.h3_cell:
            continue
        try:
            a.h3_cell = h3.latlng_to_cell(a.lat, a.lng, 10)
            a.save(update_fields=["h3_cell"])
        except Exception:
            continue


def reverse_junction_slugs(apps, schema_editor):
    Junction = apps.get_model("accidents", "Junction")
    Junction.objects.update(slug="")


def reverse_h3_cells(apps, schema_editor):
    Accident = apps.get_model("accidents", "Accident")
    Accident.objects.update(h3_cell="")


class Migration(migrations.Migration):
    dependencies = [
        ("accidents", "0003_add_slug_h3_cell"),
    ]
    operations = [
        migrations.RunPython(backfill_junction_slugs, reverse_junction_slugs),
        migrations.RunPython(backfill_h3_cells, reverse_h3_cells),
    ]
