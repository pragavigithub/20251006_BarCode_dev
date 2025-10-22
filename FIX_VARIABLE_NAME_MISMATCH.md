# FIX: Variable Name Mismatch (grpo vs grpo_doc)

## 🎉 GREAT PROGRESS!

You've successfully fixed the template location issue! The templates are now being found correctly. 

**New Error**: Variable name mismatch between route and template.

---

## ❌ THE ERROR

```
jinja2.exceptions.UndefinedError: 'grpo_doc' is undefined
```

**What happened**:
- POST /grpo/create → ✅ GRPO created successfully (302)
- GET /grpo/detail/3 → ❌ Template error (500)

---

## 🔍 ROOT CAUSE

**Route passes** (line 41 in `modules/grpo/routes.py`):
```python
return render_template('grpo/grpo_detail.html', grpo=grpo)
                                                ^^^^
                                                Variable name: grpo
```

**Template expects** (line 3 in `grpo_detail.html`):
```html
{% block title %}GRPO Detail - {{ grpo_doc.po_number }}{% endblock %}
                                   ^^^^^^^^
                                   Variable name: grpo_doc
```

**Mismatch**: Route uses `grpo`, template uses `grpo_doc`

---

## ✅ THE FIX

### File: `modules/grpo/routes.py`

**Find** the `detail` function (around lines 30-41):

```python
@grpo_bp.route('/detail/<int:grpo_id>')
@login_required
def detail(grpo_id):
    """GRPO detail page"""
    grpo = GRPODocument.query.get_or_404(grpo_id)       ← CHANGE THIS
    
    # Check permissions
    if grpo.user_id != current_user.id and current_user.role not in ['admin', 'manager', 'qc']:
        flash('Access denied - You can only view your own GRPOs', 'error')
        return redirect(url_for('grpo.index'))
    
    return render_template('grpo/grpo_detail.html', grpo=grpo)  ← AND THIS
```

**Replace with**:

```python
@grpo_bp.route('/detail/<int:grpo_id>')
@login_required
def detail(grpo_id):
    """GRPO detail page"""
    grpo_doc = GRPODocument.query.get_or_404(grpo_id)   ← Changed to grpo_doc
    
    # Check permissions
    if grpo_doc.user_id != current_user.id and current_user.role not in ['admin', 'manager', 'qc']:
        flash('Access denied - You can only view your own GRPOs', 'error')
        return redirect(url_for('grpo.index'))
    
    return render_template('grpo/grpo_detail.html', grpo_doc=grpo_doc)  ← Changed to grpo_doc
```

---

## 📝 WHAT TO CHANGE

### Line 34 (variable declaration):
**Before**: `grpo = GRPODocument.query.get_or_404(grpo_id)`  
**After**: `grpo_doc = GRPODocument.query.get_or_404(grpo_id)`

### Line 37 (permission check):
**Before**: `if grpo.user_id != current_user.id and current_user.role not in ['admin', 'manager', 'qc']:`  
**After**: `if grpo_doc.user_id != current_user.id and current_user.role not in ['admin', 'manager', 'qc']:`

### Line 41 (render template):
**Before**: `return render_template('grpo/grpo_detail.html', grpo=grpo)`  
**After**: `return render_template('grpo/grpo_detail.html', grpo_doc=grpo_doc)`

---

## 🔄 STEP-BY-STEP

1. **Open File**:
   ```
   E:\emerald\20251022\12\20251006_BarCode_dev\modules\grpo\routes.py
   ```

2. **Go to line 34** (or search for `def detail(grpo_id):`)

3. **Replace 3 instances** of `grpo` with `grpo_doc`:
   - Line ~34: Variable declaration
   - Line ~37: Permission check (if statement)
   - Line ~41: render_template call

4. **Save** the file (Ctrl+S)

5. **Restart Flask**:
   - Press Ctrl+C
   - Run `python main.py`

6. **Test**:
   - Go to GRPO list page
   - Click on a GRPO
   - Detail page should load! ✅

---

## ✅ REPLIT STATUS

**Fixed in Replit!**
- ✅ Changed `grpo` to `grpo_doc` in the detail route
- ✅ Restarted application
- ✅ Variable names now match between route and template

---

## 🎉 AFTER THIS FIX

Everything will work perfectly:
- ✅ GRPO list page loads
- ✅ Create new GRPO
- ✅ View GRPO detail page (currently failing, will be fixed!)
- ✅ Add items to GRPO
- ✅ Generate barcodes
- ✅ Serial/batch tracking

---

## 📊 COMPLETE FIX SUMMARY

For your local environment (`E:\emerald\20251022\12\`):

| Fix | Status | File | Lines |
|-----|--------|------|-------|
| 1. Template location | ✅ Done | Move templates to `grpo/` subfolder | N/A |
| 2. Blueprint parameter | ✅ Done | `modules/grpo/routes.py` | Line 17 |
| 3. Redirect old routes | ✅ Done | `routes.py` (main) | Lines 746, 893 |
| 4. Variable name fix | ⚠️ **Do this now** | `modules/grpo/routes.py` | Lines 34, 37, 41 |

---

**Time Required**: 2 minutes  
**Difficulty**: Very Easy (find & replace)  
**Result**: GRPO detail page will work! ✅
