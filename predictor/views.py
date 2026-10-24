from pathlib import Path

import pandas as pd
from django.shortcuts import redirect, render
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

DATASET_PATH = Path(__file__).resolve().parent / 'ml_model' / 'e_waste_value_dataset.csv'
MODEL = None


def _load_dataset():
    return pd.read_csv(DATASET_PATH)


def _get_model():
    global MODEL
    if MODEL is not None:
        return MODEL

    df = _load_dataset()
    X = df.drop(columns=['estimated_value'])
    y = df['estimated_value']

    numeric_cols = [col for col in X.columns if pd.api.types.is_numeric_dtype(X[col])]
    categorical_cols = [col for col in X.columns if col not in numeric_cols]

    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), numeric_cols),
            ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_cols),
        ]
    )

    MODEL = Pipeline([
        ('preprocessor', preprocessor),
        ('regressor', RandomForestRegressor(n_estimators=400, random_state=42)),
    ])
    MODEL.fit(X, y)
    return MODEL


def _get_choices(column_name):
    values = _load_dataset()[column_name].dropna().astype(str).unique().tolist()
    return sorted(values)


def _prediction_history(request):
    history = request.session.get('prediction_history', [])
    request.session['prediction_history'] = history
    return history


def _prepare_prediction_payload(request):
    payload = {
        'category': request.POST.get('category', ''),
        'device_type': request.POST.get('device_type', ''),
        'weight_kg': float(request.POST.get('weight_kg', 0) or 0),
        'condition': request.POST.get('condition', ''),
        'age_years': int(request.POST.get('age_years', 0) or 0),
        'brand': request.POST.get('brand', ''),
        'quantity': int(request.POST.get('quantity', 0) or 0),
    }
    return payload


def _predict_value(payload):
    model = _get_model()
    frame = pd.DataFrame([payload])
    prediction = model.predict(frame)[0]
    return round(float(prediction), 2)


def home(request):
    return render(request, 'home.html')


def login_view(request):
    if request.method == 'POST':
        return redirect('dashboard')
    return render(request, 'login.html')


def register_view(request):
    if request.method == 'POST':
        return redirect('dashboard')
    return render(request, 'register.html')


def dashboard(request):
    df = _load_dataset()
    context = {
        'record_count': len(df),
        'average_value': round(float(df['estimated_value'].mean()), 2),
        'top_category': df['category'].value_counts().idxmax(),
        'history_count': len(_prediction_history(request)),
    }
    return render(request, 'dashboard.html', context)


def prediction_form(request):
    categories = _get_choices('category')
    conditions = _get_choices('condition')
    brands = _get_choices('brand')
    device_types = _get_choices('device_type')

    if request.method == 'POST':
        payload = _prepare_prediction_payload(request)
        errors = []

        if not payload['category']:
            errors.append('Select a category.')
        if not payload['device_type']:
            errors.append('Select a device type.')
        if payload['weight_kg'] <= 0:
            errors.append('Weight must be greater than zero.')
        if payload['quantity'] <= 0:
            errors.append('Quantity must be at least one.')

        if errors:
            return render(
                request,
                'prediction_form.html',
                {
                    'categories': categories,
                    'conditions': conditions,
                    'brands': brands,
                    'device_types': device_types,
                    'errors': errors,
                    'form_data': payload,
                },
            )

        prediction_value = _predict_value(payload)
        history = _prediction_history(request)
        entry = {
            'id': len(history) + 1,
            'category': payload['category'],
            'device_type': payload['device_type'],
            'weight_kg': payload['weight_kg'],
            'condition': payload['condition'],
            'age_years': payload['age_years'],
            'brand': payload['brand'],
            'quantity': payload['quantity'],
            'estimated_value': prediction_value,
        }
        history.insert(0, entry)
        request.session['prediction_history'] = history
        request.session.modified = True

        return render(
            request,
            'prediction_form.html',
            {
                'categories': categories,
                'conditions': conditions,
                'brands': brands,
                'device_types': device_types,
                'prediction': entry,
                'form_data': payload,
            },
        )

    return render(
        request,
        'prediction_form.html',
        {
            'categories': categories,
            'conditions': conditions,
            'brands': brands,
            'device_types': device_types,
        },
    )


def history(request):
    context = {'history': _prediction_history(request)}
    return render(request, 'history.html', context)


def profile(request):
    return render(request, 'profile.html', {'user_name': 'Demo User'})


def edit_prediction(request, prediction_id):
    history_items = _prediction_history(request)
    prediction = next((item for item in history_items if item.get('id') == int(prediction_id)), None)

    if prediction is None:
        return redirect('history')

    if request.method == 'POST':
        payload = _prepare_prediction_payload(request)
        updated_value = _predict_value(payload)
        prediction.update({
            'category': payload['category'],
            'device_type': payload['device_type'],
            'weight_kg': payload['weight_kg'],
            'condition': payload['condition'],
            'age_years': payload['age_years'],
            'brand': payload['brand'],
            'quantity': payload['quantity'],
            'estimated_value': updated_value,
        })
        request.session['prediction_history'] = history_items
        request.session.modified = True
        return redirect('history')

    context = {
        'prediction': prediction,
        'categories': _get_choices('category'),
        'conditions': _get_choices('condition'),
        'brands': _get_choices('brand'),
        'device_types': _get_choices('device_type'),
    }
    return render(request, 'edit_prediction.html', context)
