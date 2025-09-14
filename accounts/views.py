from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import CreateView, FormView, TemplateView
from django.urls import reverse_lazy
from django.http import HttpResponse
from .forms import RegistrationForm, OrganizationCreationForm, InviteMemberForm
from .models import CustomUser
from core.models import Organization, UserProfile


class AccountTypeSelectionView(TemplateView):
    """First step: Let user choose between personal or business account"""
    template_name = 'accounts/account_type_selection.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Choose Account Type'
        return context


class PersonalRegistrationView(CreateView):
    """Personal account registration - single step for individuals"""
    form_class = RegistrationForm
    template_name = 'accounts/personal_register.html'
    success_url = reverse_lazy('homepage:index')

    def form_valid(self, form):
        user = form.save()
        login(self.request, user, backend='django.contrib.auth.backends.ModelBackend')
        
        # Create a personal workspace for the user
        org_name = f"{user.first_name} {user.last_name}'s Workspace" if user.first_name and user.last_name else f"{user.username}'s Workspace"
        organization = Organization.objects.create(
            name=org_name,
            description=f"Personal workspace for {user.get_full_name() or user.username}",
            organization_type='personal',
            is_active=True
        )
        
        # Create user profile
        UserProfile.objects.create(
            user=user,
            organization=organization,
            is_organization_admin=True,
            has_staff_panel_access=True,
            can_create_organizations=False  # Personal users can't create more orgs
        )
        
        messages.success(self.request, f'Welcome {user.first_name or user.username}! Your personal workspace has been created.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Personal Account'
        return context


class BusinessRegistrationView(CreateView):
    """Business account registration - first step of multi-step process"""
    form_class = RegistrationForm
    template_name = 'accounts/business_register.html'
    
    def dispatch(self, request, *args, **kwargs):
        """If user is already logged in, redirect to organization creation"""
        if request.user.is_authenticated:
            # Check if user already has an organization
            try:
                profile = request.user.mediap_profile
                if profile.organization.organization_type == 'business':
                    messages.info(request, f'You already belong to the business organization: {profile.organization.name}')
                    return redirect('dashboard:dashboard')
                elif profile.organization.organization_type == 'personal':
                    # Allow personal users to upgrade to business
                    messages.info(request, 'Upgrade your personal workspace to a business organization.')
                    return redirect('accounts:upgrade_to_business')
            except:
                # User has no profile, allow them to create organization
                pass
            
            # User is logged in but has no organization, redirect to org creation
            messages.info(request, 'Create your business organization.')
            return redirect('accounts:create_organization')
        
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        user = form.save()
        login(self.request, user, backend='django.contrib.auth.backends.ModelBackend')
        
        # Store account type in session for next steps
        self.request.session['account_type'] = 'business'
        self.request.session['registration_step'] = 'organization'
        
        messages.success(self.request, f'Welcome {user.first_name or user.username}! Now let\'s set up your organization.')
        
        # Custom redirect instead of using success_url
        return redirect('accounts:create_organization')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Business Account'
        return context


class OrganizationCreationView(CreateView):
    """Organization creation for business accounts - step 2"""
    form_class = OrganizationCreationForm
    template_name = 'accounts/create_organization.html'
    success_url = reverse_lazy('accounts:invite_members')

    def form_invalid(self, form):
        messages.error(self.request, 'Please correct the errors below and try again.')
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'{field}: {error}')
        return super().form_invalid(form)

    def form_valid(self, form):
        # Make sure user is authenticated, if not, this shouldn't be processed
        if not self.request.user.is_authenticated:
            messages.error(self.request, 'You must be logged in to create an organization.')
            return redirect('accounts:business_register')
        
        # Check if user already has an organization profile
        try:
            existing_profile = self.request.user.mediap_profile
            if existing_profile.organization.organization_type == 'business':
                messages.error(
                    self.request, 
                    f'You already belong to a business organization: "{existing_profile.organization.name}". '
                )
                return redirect('dashboard:dashboard')
            elif existing_profile.organization.organization_type == 'personal':
                # Allow upgrading from personal to business
                messages.info(self.request, 'Upgrading your personal workspace to a business organization.')
                existing_profile.organization.organization_type = 'business'
                existing_profile.organization.name = form.cleaned_data['name']
                existing_profile.organization.description = form.cleaned_data.get('description', '')
                existing_profile.organization.save()
                
                # Update user permissions
                existing_profile.can_create_organizations = True
                existing_profile.save()
                
                messages.success(self.request, f'Successfully upgraded to business organization: {existing_profile.organization.name}')
                return redirect('dashboard:dashboard')
        except UserProfile.DoesNotExist:
            # User doesn't have a profile yet, create new organization and profile
            pass
            
        try:
            # Create new business organization
            organization = Organization.objects.create(
                name=form.cleaned_data['name'],
                description=form.cleaned_data.get('description', ''),
                organization_type='business',
                is_active=True
            )
            
            # Create user profile as organization admin
            UserProfile.objects.create(
                user=self.request.user,
                organization=organization,
                is_organization_admin=True,
                has_staff_panel_access=True,
                can_create_organizations=True  # Business users can create more orgs
            )
            
            messages.success(self.request, f'Successfully created business organization: {organization.name}')
            return redirect('dashboard:dashboard')
            
        except Exception as e:
            messages.error(self.request, f'Error creating organization: {str(e)}')
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Your Organization'
        context['step'] = 2
        return context


class InviteMembersView(FormView):
    """Team member invitation - step 3 (optional)"""
    form_class = InviteMemberForm
    template_name = 'accounts/invite_members.html'
    success_url = reverse_lazy('homepage:index')

    def dispatch(self, request, *args, **kwargs):
        # Ensure user is logged in and has an organization
        if not request.user.is_authenticated:
            return redirect('accounts:register')
        
        # Check if user has an organization profile
        try:
            profile = request.user.mediap_profile
            if not profile.is_organization_admin:
                messages.error(request, 'You need to be an organization admin to invite members.')
                return redirect('dashboard:dashboard')
        except UserProfile.DoesNotExist:
            messages.error(request, 'Please set up your organization first.')
            return redirect('core:setup_organization')
        
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        # Get the user's organization
        try:
            profile = self.request.user.mediap_profile
            organization = profile.organization
        except UserProfile.DoesNotExist:
            messages.error(self.request, 'Organization not found.')
            return redirect('core:setup_organization')

        email_list = form.cleaned_data['email_list'].strip()
        if email_list:
            emails = [email.strip() for email in email_list.split('\n') if email.strip()]
            
            # TODO: Send actual invitation emails
            # For now, just show success message
            messages.success(
                self.request, 
                f'Invitations will be sent to {len(emails)} team members. '
                f'(Note: Email sending is not yet implemented - this is a placeholder.)'
            )
        else:
            messages.info(self.request, 'You can invite team members later from your organization settings.')

        # Clean up session
        self.request.session.pop('organization_id', None)
        self.request.session.pop('account_type', None)
        self.request.session.pop('registration_step', None)

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Invite Team Members'
        context['step'] = 3
        
        # Get the organization name for display
        organization_id = self.request.session.get('organization_id')
        if organization_id:
            try:
                organization = Organization.objects.get(id=organization_id, owner=self.request.user)
                context['organization'] = organization
            except Organization.DoesNotExist:
                pass
        
        return context

    def get(self, request, *args, **kwargs):
        # Allow users to skip this step
        if request.GET.get('skip'):
            messages.info(request, 'You can invite team members later from your organization settings.')
            # Clean up session
            request.session.pop('organization_id', None)
            request.session.pop('account_type', None)
            request.session.pop('registration_step', None)
            return redirect('homepage:index')
        
        return super().get(request, *args, **kwargs)


# Legacy views for compatibility
class RegistrationView(TemplateView):
    """Legacy registration view - now redirects to new flow"""
    def get(self, request, *args, **kwargs):
        return redirect('accounts:register')

class AccountTypeView(TemplateView):
    """Legacy account type view - now redirects to new flow"""
    def get(self, request, *args, **kwargs):
        return redirect('accounts:register')


@login_required
def profile_view(request):
    """User profile view with organization information"""
    # Get user's organization
    try:
        profile = request.user.mediap_profile
        user_orgs = [profile.organization]
    except UserProfile.DoesNotExist:
        user_orgs = []
    
    context = {
        'user': request.user,
        'organizations': user_orgs,
    }
    
    return render(request, 'accounts/profile.html', context)


@login_required
def upgrade_to_business(request):
    """Simple redirect to organization creation for business upgrade"""
    messages.info(request, 'Create your business organization to unlock team features.')
    return redirect('accounts:create_organization')


class LoginView(TemplateView):
    """Custom login view"""
    template_name = 'accounts/login.html'
    
    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if username and password:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                messages.success(request, f'Welcome back, {user.first_name or user.username}!')
                
                # Redirect to next URL if provided, otherwise to profile
                next_url = request.GET.get('next', '/')
                return redirect(next_url)
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Please enter both username and password.')
        
        return render(request, self.template_name)


def logout_view(request):
    """Custom logout view"""
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('homepage:index')
