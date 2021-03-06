# -*- mode: python; encoding: utf-8 -*-
#
# Copyright 2014 the Critic contributors, Opera Software ASA
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License.  You may obtain a copy of
# the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  See the
# License for the specific language governing permissions and limitations under
# the License.

import api
import jsonapi

@jsonapi.PrimaryResource
class Branches(object):
    """Branches in the Git repositories."""

    name = "branches"
    contexts = (None, "repositories")
    value_class = api.branch.Branch
    exceptions = (api.branch.BranchError, api.repository.RepositoryError)

    @staticmethod
    def json(value, parameters, linked):
        """{
             "id": integer, // the branch's id
             "name": string, // the branch's name
             "repository": integer, // the branch's repository's id
             "head": integer, // the branch's head commit's id
           }"""

        linked.add("repositories", value.repository.id)
        linked.add("commits", value.head)

        return parameters.filtered(
            "branches", { "id": value.id,
                          "name": value.name,
                          "repository": value.repository.id,
                          "head": value.head.id })

    @staticmethod
    def single(critic, context, argument, parameters):
        """Retrieve one (or more) branches in the Git repositories.

           BRANCH_ID : integer

           Retrieve a branch identified by its unique numeric id."""

        return api.branch.fetch(critic, branch_id=jsonapi.numeric_id(argument))

    @staticmethod
    def multiple(critic, context, parameters):
        """Retrieve all branches in the Git repositories.

           repository : REPOSITORY : -

           Include only branches in one repository, identified by the
           repository's unique numeric id or short-name.

           name : NAME : string

           Retrieve only the branch with the specified name.  The name should
           <em>not</em> include the "refs/heads/" prefix.  When this parameter
           is specified a repository must be specified as well, either in the
           resource path or using the <code>repository</code> parameter."""

        repository = jsonapi.v1.repositories.Repositories.deduce(
            critic, context, parameters)
        name_parameter = parameters.getQueryParameter("name")
        if name_parameter:
            if repository is None:
                raise jsonapi.UsageError(
                    "Named branch access must have repository specified.")
            return api.branch.fetch(
                critic, repository=repository, name=name_parameter)
        return api.branch.fetchAll(critic, repository=repository)

import commits

@jsonapi.PrimaryResource
class BranchCommits(object):
    """Commits associated with a branch.

       This is typically not all commits reachable from a branch.  When a branch
       is first pushed to a repository, all commits reachable only from the
       branch are associated with it.  After that, as the branch is updated, all
       new commits are also associated with the branch."""

    name = "commits"
    contexts = ("branches",)
    value_class = api.commit.Commit
    exceptions = (api.commit.CommitError,)

    json = staticmethod(commits.Commits.json)

    @staticmethod
    def multiple(critic, context, parameters):
        """Retrieve all commits associated with the branch.

           sort : SORT_KEY : -

           Sort the commits in <code>topological</code> or <code>date</code>
           order.  In either case, a child commit is always sorted before all of
           its parent commits, but whenever more than one commit could be
           emitted without violating this rule, topological order prefers the
           first parent and its ancestors, while date order prefers the commit
           with the most recent commit date.  Topological order is the
           default."""

        assert isinstance(context, api.branch.Branch)
        sort_parameter = parameters.getQueryParameter("sort")
        if sort_parameter is None or sort_parameter == "topological":
            return context.commits.topo_ordered
        elif sort_parameter != "date":
            raise jsonapi.UsageError("Invalid commits sort parameter: %r"
                                     % sort_parameter)
        return context.commits.date_ordered
