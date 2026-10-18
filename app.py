import os
import io
from datetime import datetime, date
from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, session, jsonify, send_file, abort, g
)

from config import config
from database import init_db, close_db, update_overdue_statuses
from services.auth_service import (
    authenticate_admin, login_user, logout_user, is_authenticated,
    login_required, generate_csrf_token, validate_csrf_token
)
from services.book_service import (
    get_all_books, get_book_by_id, add_book, update_book,
    delete_book, get_categories, get_featured_books
)
from services.member_service import (
    get_all_members, get_member_by_id, add_member,
    update_member, delete_member, get_member_borrowing_history
)
from services.borrowing_service import (
    issue_book, return_book, get_all_borrowings, get_borrowing_by_id
)
from services.analytics_service import (
    get_dashboard_metrics, get_category_analytics,
    get_top_borrowed_books, get_monthly_borrowing_trends,
    get_duration_and_overdue_stats
)
from services.export_service import (
    get_books_dataframe, get_members_dataframe, get_borrowings_dataframe,
    export_to_csv, export_to_excel, generate_comprehensive_excel
)

def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'production' if os.environ.get('RENDER') else 'development')

    app = Flask(__name__)
    app.config.from_object(config.get(config_name, config['default']))

    # Ensure instance and exports directories exist
    os.makedirs(os.path.dirname(app.config['DATABASE']), exist_ok=True)
    os.makedirs(app.config['EXPORTS_DIR'], exist_ok=True)

    # Initialize database tables on app creation
    init_db(app.config['DATABASE'])

    # Register teardown
    app.teardown_appcontext(close_db)

    # Inject helper variables into all Jinja templates
    @app.context_processor
    def inject_globals():
        return {
            'csrf_token': generate_csrf_token,
            'is_authenticated': is_authenticated,
            'current_admin': session.get('admin_name'),
            'current_admin_username': session.get('admin_username'),
            'current_year': datetime.now().year,
            'today_date': date.today().isoformat()
        }

    # Synchronize overdue statuses periodically or on request
    @app.before_request
    def check_overdue_and_csrf():
        # Validate CSRF for POST, PUT, DELETE, PATCH
        if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
            # Allow skipping CSRF in testing environment if configured
            if not app.config.get('TESTING') or app.config.get('WTF_CSRF_ENABLED', True):
                token = request.form.get('csrf_token') or request.headers.get('X-CSRFToken')
                if not validate_csrf_token(token):
                    abort(400, description="Invalid or missing CSRF security token.")

    # ==========================================
    # PUBLIC ROUTES
    # ==========================================

    @app.route('/')
    def index():
        """Cinematic Homepage with 3D Hero, floating books, live stats, and featured catalog."""
        update_overdue_statuses(app.config['DATABASE'])
        metrics = get_dashboard_metrics(app.config['DATABASE'])
        featured_books = get_featured_books(limit=6, db_path=app.config['DATABASE'])
        categories = get_categories(app.config['DATABASE'])
        return render_template(
            'index.html',
            metrics=metrics,
            featured_books=featured_books,
            categories=categories
        )

    @app.route('/books')
    def books_catalog():
        """Public book catalog with search, filtering, sorting, and pagination."""
        search = request.args.get('search', '').strip()
        category = request.args.get('category', '').strip()
        availability = request.args.get('availability', '').strip()
        sort_by = request.args.get('sort_by', 'title').strip()
        order = request.args.get('order', 'asc').strip()
        page = request.args.get('page', 1, type=int)

        catalog_data = get_all_books(
            search=search,
            category=category,
            availability=availability,
            sort_by=sort_by,
            order=order,
            page=page,
            per_page=12,
            db_path=app.config['DATABASE']
        )
        categories = get_categories(app.config['DATABASE'])

        return render_template(
            'books.html',
            books=catalog_data['books'],
            total=catalog_data['total'],
            page=catalog_data['page'],
            total_pages=catalog_data['total_pages'],
            categories=categories,
            current_category=category,
            current_search=search,
            current_availability=availability,
            current_sort=sort_by,
            current_order=order
        )

    @app.route('/books/<int:book_id>')
    def book_details(book_id):
        """Dedicated detail view for a specific book."""
        book = get_book_by_id(book_id, db_path=app.config['DATABASE'])
        if not book:
            flash("The requested book could not be found.", "warning")
            return redirect(url_for('books_catalog'))
        return render_template('book_details.html', book=book)

    @app.route('/about')
    def about():
        """About LibraVerse platform and technological architecture."""
        return render_template('about.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """Administrator login interface."""
        if is_authenticated():
            return redirect(url_for('dashboard'))

        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '').strip()

            admin = authenticate_admin(username, password, db_path=app.config['DATABASE'])
            if admin:
                login_user(admin)
                flash(f"Welcome back, {admin['full_name']}! Access granted to command console.", "success")
                next_url = request.args.get('next') or url_for('dashboard')
                return redirect(next_url)
            else:
                flash("Invalid username/email or password. Access denied.", "danger")

        return render_template('login.html')

    @app.route('/logout')
    def logout():
        """Terminate administrative session."""
        logout_user()
        flash("You have been securely logged out.", "info")
        return redirect(url_for('index'))

    # ==========================================
    # PROTECTED ADMINISTRATOR ROUTES
    # ==========================================

    @app.route('/admin/dashboard')
    @login_required
    def dashboard():
        """Main administrator command center with metrics and Chart.js analytics."""
        update_overdue_statuses(app.config['DATABASE'])
        metrics = get_dashboard_metrics(app.config['DATABASE'])
        category_data = get_category_analytics(app.config['DATABASE'])
        top_books = get_top_borrowed_books(limit=6, db_path=app.config['DATABASE'])
        monthly_trends = get_monthly_borrowing_trends(app.config['DATABASE'])
        duration_stats = get_duration_and_overdue_stats(app.config['DATABASE'])
        recent_borrowings = get_all_borrowings(db_path=app.config['DATABASE'])[:8]

        return render_template(
            'dashboard.html',
            metrics=metrics,
            category_data=category_data,
            top_books=top_books,
            monthly_trends=monthly_trends,
            duration_stats=duration_stats,
            recent_borrowings=recent_borrowings
        )

    # --- Book Management ---

    @app.route('/admin/books')
    @login_required
    def manage_books():
        """Administrator book inventory table with search, add, edit, and delete options."""
        search = request.args.get('search', '').strip()
        category = request.args.get('category', '').strip()
        page = request.args.get('page', 1, type=int)

        data = get_all_books(
            search=search,
            category=category,
            sort_by='id',
            order='desc',
            page=page,
            per_page=15,
            db_path=app.config['DATABASE']
        )
        categories = get_categories(app.config['DATABASE'])

        return render_template(
            'manage_books.html',
            books=data['books'],
            total=data['total'],
            page=data['page'],
            total_pages=data['total_pages'],
            categories=categories,
            search=search,
            current_category=category
        )

    @app.route('/admin/books/add', methods=['POST'])
    @login_required
    def add_book_route():
        """Handle new book creation."""
        try:
            book_id = add_book(request.form, db_path=app.config['DATABASE'])
            flash(f"Book '{request.form.get('title')}' added to library catalog successfully!", "success")
        except ValueError as ve:
            flash(str(ve), "danger")
        except Exception as e:
            flash(f"Database error while adding book: {str(e)}", "danger")

        return redirect(url_for('manage_books'))

    @app.route('/admin/books/<int:book_id>/edit', methods=['POST'])
    @login_required
    def edit_book_route(book_id):
        """Handle existing book modifications."""
        try:
            update_book(book_id, request.form, db_path=app.config['DATABASE'])
            flash("Book details updated successfully!", "success")
        except ValueError as ve:
            flash(str(ve), "danger")
        except Exception as e:
            flash(f"Failed to update book: {str(e)}", "danger")

        return redirect(url_for('manage_books'))

    @app.route('/admin/books/<int:book_id>/delete', methods=['POST'])
    @login_required
    def delete_book_route(book_id):
        """Safely delete a book if no copies are actively borrowed."""
        try:
            delete_book(book_id, db_path=app.config['DATABASE'])
            flash("Book removed from inventory successfully.", "success")
        except ValueError as ve:
            flash(str(ve), "warning")
        except Exception as e:
            flash(f"Error deleting book: {str(e)}", "danger")

        return redirect(url_for('manage_books'))

    # --- Member Management ---

    @app.route('/admin/members')
    @login_required
    def manage_members():
        """Member directory and registration control."""
        search = request.args.get('search', '').strip()
        status = request.args.get('status', '').strip()

        members = get_all_members(
            search=search,
            status=status,
            sort_by='id',
            order='desc',
            db_path=app.config['DATABASE']
        )
        return render_template(
            'manage_members.html',
            members=members,
            search=search,
            status=status
        )

    @app.route('/admin/members/add', methods=['POST'])
    @login_required
    def add_member_route():
        """Register a new member."""
        try:
            member_id = add_member(request.form, db_path=app.config['DATABASE'])
            flash(f"Member '{request.form.get('full_name')}' registered successfully!", "success")
        except ValueError as ve:
            flash(str(ve), "danger")
        except Exception as e:
            flash(f"Failed to register member: {str(e)}", "danger")

        return redirect(url_for('manage_members'))

    @app.route('/admin/members/<int:member_id>/edit', methods=['POST'])
    @login_required
    def edit_member_route(member_id):
        """Update member profile."""
        try:
            update_member(member_id, request.form, db_path=app.config['DATABASE'])
            flash("Member details updated successfully!", "success")
        except ValueError as ve:
            flash(str(ve), "danger")
        except Exception as e:
            flash(f"Failed to update member: {str(e)}", "danger")

        return redirect(url_for('manage_members'))

    @app.route('/admin/members/<int:member_id>/delete', methods=['POST'])
    @login_required
    def delete_member_route(member_id):
        """Safely delete member if no unreturned books exist."""
        try:
            delete_member(member_id, db_path=app.config['DATABASE'])
            flash("Member record deleted successfully.", "success")
        except ValueError as ve:
            flash(str(ve), "warning")
        except Exception as e:
            flash(f"Error removing member: {str(e)}", "danger")

        return redirect(url_for('manage_members'))

    @app.route('/admin/members/<int:member_id>/history')
    @login_required
    def member_history(member_id):
        """View a specific member's loan history."""
        member = get_member_by_id(member_id, db_path=app.config['DATABASE'])
        if not member:
            flash("Member not found.", "warning")
            return redirect(url_for('manage_members'))

        history = get_member_borrowing_history(member_id, db_path=app.config['DATABASE'])
        return render_template('member_history.html', member=member, history=history)

    # --- Circulation: Issue & Return ---

    @app.route('/admin/circulation')
    @login_required
    def issue_return():
        """Circulation desk: Issue books and process returns."""
        update_overdue_statuses(app.config['DATABASE'])
        # Active books with copies available
        available_books = get_all_books(availability='available', per_page=1000, db_path=app.config['DATABASE'])['books']
        # Active registered members
        active_members = [m for m in get_all_members(db_path=app.config['DATABASE']) if m['membership_status'] == 'Active']
        # Currently issued or overdue records for return desk
        active_borrowings = [
            b for b in get_all_borrowings(db_path=app.config['DATABASE'])
            if b['status'] in ['Issued', 'Overdue']
        ]

        return render_template(
            'issue_return.html',
            available_books=available_books,
            active_members=active_members,
            active_borrowings=active_borrowings
        )

    @app.route('/admin/circulation/issue', methods=['POST'])
    @login_required
    def issue_book_route():
        """Process book checkout transaction."""
        try:
            book_id = int(request.form.get('book_id', 0))
            member_id = int(request.form.get('member_id', 0))
            issue_date = request.form.get('issue_date', date.today().isoformat())
            due_date = request.form.get('due_date', '')

            borrowing_id = issue_book(book_id, member_id, issue_date, due_date, db_path=app.config['DATABASE'])
            flash("Book successfully issued to member! Available copy count updated.", "success")
        except ValueError as ve:
            flash(str(ve), "danger")
        except Exception as e:
            flash(f"Transaction failed: {str(e)}", "danger")

        return redirect(url_for('issue_return'))

    @app.route('/admin/circulation/return/<int:borrowing_id>', methods=['POST'])
    @login_required
    def return_book_route(borrowing_id):
        """Process book check-in / return."""
        try:
            return_date = request.form.get('return_date', date.today().isoformat())
            res = return_book(borrowing_id, return_date, db_path=app.config['DATABASE'])
            if res['overdue_days'] > 0:
                flash(
                    f"Book '{res['book_title']}' returned with {res['overdue_days']} day(s) overdue. Assessed fine: ${res['fine_amount']:.2f}.",
                    "warning"
                )
            else:
                flash(f"Book '{res['book_title']}' returned on time! Copy returned to inventory.", "success")
        except ValueError as ve:
            flash(str(ve), "danger")
        except Exception as e:
            flash(f"Return operation failed: {str(e)}", "danger")

        return redirect(url_for('issue_return'))

    # --- Borrowing History ---

    @app.route('/admin/history')
    @login_required
    def borrowing_history():
        """Comprehensive transaction history log with filters and search."""
        update_overdue_statuses(app.config['DATABASE'])
        status = request.args.get('status', '').strip()
        search = request.args.get('search', '').strip()
        sort_by = request.args.get('sort_by', 'issue_date').strip()
        order = request.args.get('order', 'desc').strip()

        records = get_all_borrowings(
            status=status,
            search=search,
            sort_by=sort_by,
            order=order,
            db_path=app.config['DATABASE']
        )
        return render_template(
            'borrowing_history.html',
            records=records,
            current_status=status,
            search=search,
            sort_by=sort_by,
            order=order
        )

    # --- Analytics & Reports ---

    @app.route('/admin/analytics')
    @login_required
    def analytics():
        """Deep analytics console leveraging Pandas and NumPy statistical computations."""
        update_overdue_statuses(app.config['DATABASE'])
        metrics = get_dashboard_metrics(app.config['DATABASE'])
        category_data = get_category_analytics(app.config['DATABASE'])
        top_books = get_top_borrowed_books(limit=10, db_path=app.config['DATABASE'])
        monthly_trends = get_monthly_borrowing_trends(app.config['DATABASE'])
        duration_stats = get_duration_and_overdue_stats(app.config['DATABASE'])

        return render_template(
            'analytics.html',
            metrics=metrics,
            category_data=category_data,
            top_books=top_books,
            monthly_trends=monthly_trends,
            duration_stats=duration_stats
        )

    # --- Data Exports ---

    @app.route('/admin/export/<export_type>/<fmt>')
    @login_required
    def export_data(export_type, fmt):
        """Generate and stream CSV or Excel exports generated by Pandas."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        db_path = app.config['DATABASE']

        if export_type == 'books':
            df = get_books_dataframe(db_path)
            base_filename = f"libraverse_books_{timestamp}"
            sheet_title = "Books Inventory"
        elif export_type == 'members':
            df = get_members_dataframe(db_path)
            base_filename = f"libraverse_members_{timestamp}"
            sheet_title = "Members Directory"
        elif export_type == 'borrowings':
            df = get_borrowings_dataframe(db_path)
            base_filename = f"libraverse_transactions_{timestamp}"
            sheet_title = "Borrowing History"
        elif export_type == 'comprehensive':
            # Multi-sheet comprehensive workbook
            excel_bytes = generate_comprehensive_excel(db_path)
            return send_file(
                io.BytesIO(excel_bytes),
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=f"libraverse_comprehensive_report_{timestamp}.xlsx"
            )
        else:
            abort(404, description="Invalid export type.")

        if fmt.lower() == 'csv':
            csv_bytes = export_to_csv(df)
            return send_file(
                io.BytesIO(csv_bytes),
                mimetype='text/csv',
                as_attachment=True,
                download_name=f"{base_filename}.csv"
            )
        elif fmt.lower() == 'excel':
            excel_bytes = export_to_excel({sheet_title: df})
            return send_file(
                io.BytesIO(excel_bytes),
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=f"{base_filename}.xlsx"
            )
        else:
            abort(400, description="Unsupported export format.")

    # ==========================================
    # API ENDPOINTS
    # ==========================================

    @app.route('/api/books/<int:book_id>')
    def api_book_details(book_id):
        """JSON endpoint for book details modal."""
        book = get_book_by_id(book_id, db_path=app.config['DATABASE'])
        if not book:
            return jsonify({'error': 'Book not found'}), 404
        return jsonify(book)

    # ==========================================
    # ERROR HANDLERS
    # ==========================================

    @app.errorhandler(400)
    def bad_request(e):
        return render_template('error.html', code=400, title="Bad Request", message=str(e.description if hasattr(e, 'description') else e)), 400

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('error.html', code=403, title="Access Forbidden", message="You do not have administrative permission to view this resource."), 403

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('error.html', code=404, title="Dimension Not Found", message="The stellar coordinates you requested do not exist in LibraVerse."), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('error.html', code=500, title="Core Disruption", message="A transient anomaly occurred in the quantum matrix. Our engineers are investigating."), 500

    return app

app = create_app()

if __name__ == '__main__':
    # Local development or container execution
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() in ['true', '1']
    print(f"[*] LibraVerse Portal initializing at http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)
